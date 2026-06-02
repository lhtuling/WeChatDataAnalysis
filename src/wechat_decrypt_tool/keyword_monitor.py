from __future__ import annotations

import json
import re
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional

from .app_paths import get_output_dir
from .chat_helpers import (
    _iter_message_db_paths,
    _load_contact_rows,
    _pick_display_name,
    _quote_ident,
    _resolve_msg_table_name_by_map,
    _row_to_search_hit,
    _should_keep_session,
)
from .logging_config import get_logger

logger = get_logger(__name__)

_DB_NAME = "keyword_monitor.db"
_LOCK = threading.RLock()
_MAX_KEYWORDS = 200
_MAX_KEYWORD_LEN = 200
_MAX_EXCLUDED_GROUPS = 1000
_MAX_STORED_CONTENT_LEN = 20_000


def _now_ms() -> int:
    return int(time.time() * 1000)


def _db_path() -> Path:
    return get_output_dir() / _DB_NAME


def _connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS monitor_settings (
            account TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 0,
            monitor_keywords_json TEXT NOT NULL DEFAULT '[]',
            filter_keywords_json TEXT NOT NULL DEFAULT '[]',
            excluded_groups_json TEXT NOT NULL DEFAULT '[]',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS monitor_cursors (
            account TEXT NOT NULL,
            username TEXT NOT NULL,
            db_stem TEXT NOT NULL,
            table_name TEXT NOT NULL,
            max_local_id INTEGER NOT NULL DEFAULT 0,
            updated_at INTEGER NOT NULL,
            PRIMARY KEY (account, username, db_stem, table_name)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS monitor_hits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT NOT NULL,
            username TEXT NOT NULL,
            conversation_name TEXT NOT NULL DEFAULT '',
            sender_username TEXT NOT NULL DEFAULT '',
            sender_display_name TEXT NOT NULL DEFAULT '',
            create_time INTEGER NOT NULL DEFAULT 0,
            message_id TEXT NOT NULL,
            db_stem TEXT NOT NULL,
            table_name TEXT NOT NULL,
            local_id INTEGER NOT NULL,
            server_id INTEGER NOT NULL DEFAULT 0,
            local_type INTEGER NOT NULL DEFAULT 0,
            render_type TEXT NOT NULL DEFAULT '',
            content TEXT NOT NULL DEFAULT '',
            matched_keywords_json TEXT NOT NULL DEFAULT '[]',
            is_read INTEGER NOT NULL DEFAULT 0,
            read_at INTEGER,
            created_at INTEGER NOT NULL,
            UNIQUE(account, username, message_id)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_monitor_hits_account_created ON monitor_hits(account, created_at DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_monitor_hits_account_unread ON monitor_hits(account, is_read, created_at DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_monitor_cursors_account ON monitor_cursors(account)")
    conn.commit()


def _loads_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    try:
        parsed = json.loads(str(value or "") or "[]")
    except Exception:
        return []
    return parsed if isinstance(parsed, list) else []


def _dumps_list(value: list[Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def normalize_keywords(value: Any) -> list[str]:
    if isinstance(value, str):
        parts = re.split(r"[\n\r,，;；]+", value)
    elif isinstance(value, (list, tuple)):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.extend(re.split(r"[\n\r,，;；]+", item))
            else:
                parts.append(str(item or ""))
    else:
        parts = []

    out: list[str] = []
    seen: set[str] = set()
    for item in parts:
        text = re.sub(r"\s+", " ", str(item or "").strip())
        if not text:
            continue
        text = text[:_MAX_KEYWORD_LEN]
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) >= _MAX_KEYWORDS:
            break
    return out


def normalize_excluded_groups(value: Any) -> list[dict[str, str]]:
    raw = _loads_list(value)
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw:
        if isinstance(item, dict):
            username = str(item.get("username") or "").strip()
            name = str(item.get("name") or item.get("displayName") or "").strip()
        else:
            username = str(item or "").strip()
            name = ""
        if not username or username in seen:
            continue
        seen.add(username)
        out.append({"username": username, "name": name or username})
        if len(out) >= _MAX_EXCLUDED_GROUPS:
            break
    return out


def _row_to_settings(row: Optional[sqlite3.Row], account: str) -> dict[str, Any]:
    if row is None:
        return {
            "status": "success",
            "account": account,
            "enabled": False,
            "monitorKeywords": [],
            "filterKeywords": [],
            "excludedGroups": [],
        }
    return {
        "status": "success",
        "account": account,
        "enabled": bool(int(row["enabled"] or 0)),
        "monitorKeywords": normalize_keywords(_loads_list(row["monitor_keywords_json"])),
        "filterKeywords": normalize_keywords(_loads_list(row["filter_keywords_json"])),
        "excludedGroups": normalize_excluded_groups(_loads_list(row["excluded_groups_json"])),
    }


def get_settings(account: str) -> dict[str, Any]:
    account_name = str(account or "").strip()
    if not account_name:
        return _row_to_settings(None, "")
    with _LOCK:
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = _connect()
            row = conn.execute(
                "SELECT * FROM monitor_settings WHERE account = ? LIMIT 1",
                (account_name,),
            ).fetchone()
            return _row_to_settings(row, account_name)
        finally:
            if conn is not None:
                conn.close()


def _load_sessions(account_dir: Path) -> dict[str, dict[str, Any]]:
    session_db_path = account_dir / "session.db"
    if not session_db_path.exists():
        return {}

    conn = sqlite3.connect(str(session_db_path))
    conn.row_factory = sqlite3.Row
    try:
        try:
            rows = conn.execute("SELECT username FROM SessionTable").fetchall()
        except Exception:
            rows = []
    finally:
        conn.close()

    usernames: list[str] = []
    for row in rows:
        username = str(row["username"] or "").strip()
        if not username:
            continue
        if not _should_keep_session(username, include_official=True):
            continue
        usernames.append(username)

    contact_rows = _load_contact_rows(account_dir / "contact.db", usernames)
    sessions: dict[str, dict[str, Any]] = {}
    for username in usernames:
        display_name = _pick_display_name(contact_rows.get(username), username)
        sessions[username] = {
            "username": username,
            "name": display_name or username,
            "isGroup": username.endswith("@chatroom"),
        }
    return sessions


def list_groups(account_dir: Path) -> dict[str, Any]:
    sessions = _load_sessions(account_dir)
    groups = [
        {"username": info["username"], "name": info["name"]}
        for info in sessions.values()
        if bool(info.get("isGroup"))
    ]
    groups.sort(key=lambda item: (str(item.get("name") or ""), str(item.get("username") or "")))
    return {"status": "success", "account": account_dir.name, "groups": groups}


def _has_cursors(conn: sqlite3.Connection, account: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM monitor_cursors WHERE account = ? LIMIT 1",
        (account,),
    ).fetchone()
    return row is not None


def _clear_cursors(conn: sqlite3.Connection, account: str) -> None:
    conn.execute("DELETE FROM monitor_cursors WHERE account = ?", (account,))


def _initialize_account_baseline(conn: sqlite3.Connection, account_dir: Path) -> int:
    account = account_dir.name
    sessions = _load_sessions(account_dir)
    if not sessions:
        return 0

    now = _now_ms()
    wrote = 0
    for db_path in _iter_message_db_paths(account_dir):
        msg_conn: Optional[sqlite3.Connection] = None
        try:
            msg_conn = sqlite3.connect(str(db_path))
            msg_conn.row_factory = sqlite3.Row
            rows = msg_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            names = [str(row[0] or "").strip() for row in rows if row and row[0]]
            lower_to_actual = {name.lower(): name for name in names if name}
            for username in sessions.keys():
                table_name = _resolve_msg_table_name_by_map(lower_to_actual, username)
                if not table_name:
                    continue
                try:
                    row = msg_conn.execute(
                        f"SELECT COALESCE(MAX(local_id), 0) AS mx FROM {_quote_ident(table_name)}"
                    ).fetchone()
                    max_local_id = int((row["mx"] if row is not None else 0) or 0)
                except Exception:
                    max_local_id = 0
                conn.execute(
                    """
                    INSERT INTO monitor_cursors(account, username, db_stem, table_name, max_local_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(account, username, db_stem, table_name)
                    DO UPDATE SET max_local_id = excluded.max_local_id, updated_at = excluded.updated_at
                    """,
                    (account, username, db_path.stem, table_name, int(max_local_id), now),
                )
                wrote += 1
        except Exception:
            logger.exception("[keyword-monitor] baseline failed account=%s db=%s", account, str(db_path))
            continue
        finally:
            if msg_conn is not None:
                msg_conn.close()
    return wrote


def save_settings(account_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    account = account_dir.name
    enabled = bool(payload.get("enabled"))
    monitor_keywords = normalize_keywords(payload.get("monitorKeywords", payload.get("monitor_keywords", [])))
    filter_keywords = normalize_keywords(payload.get("filterKeywords", payload.get("filter_keywords", [])))
    excluded_groups = normalize_excluded_groups(payload.get("excludedGroups", payload.get("excluded_groups", [])))
    now = _now_ms()

    with _LOCK:
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = _connect()
            prev_row = conn.execute(
                "SELECT enabled FROM monitor_settings WHERE account = ? LIMIT 1",
                (account,),
            ).fetchone()
            prev_enabled = bool(int(prev_row["enabled"] or 0)) if prev_row is not None else False

            conn.execute(
                """
                INSERT INTO monitor_settings(
                    account, enabled, monitor_keywords_json, filter_keywords_json,
                    excluded_groups_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(account) DO UPDATE SET
                    enabled = excluded.enabled,
                    monitor_keywords_json = excluded.monitor_keywords_json,
                    filter_keywords_json = excluded.filter_keywords_json,
                    excluded_groups_json = excluded.excluded_groups_json,
                    updated_at = excluded.updated_at
                """,
                (
                    account,
                    1 if enabled else 0,
                    _dumps_list(monitor_keywords),
                    _dumps_list(filter_keywords),
                    _dumps_list(excluded_groups),
                    now,
                    now,
                ),
            )

            baseline_tables = 0
            if enabled and (not prev_enabled):
                _clear_cursors(conn, account)
                baseline_tables = _initialize_account_baseline(conn, account_dir)
            elif enabled and not _has_cursors(conn, account):
                baseline_tables = _initialize_account_baseline(conn, account_dir)

            conn.commit()
            out = get_settings(account)
            out["baselineTables"] = int(baseline_tables)
            return out
        finally:
            if conn is not None:
                conn.close()


def _load_cursors(conn: sqlite3.Connection, account: str) -> dict[tuple[str, str, str], int]:
    rows = conn.execute(
        "SELECT username, db_stem, table_name, max_local_id FROM monitor_cursors WHERE account = ?",
        (account,),
    ).fetchall()
    out: dict[tuple[str, str, str], int] = {}
    for row in rows:
        key = (
            str(row["username"] or "").strip(),
            str(row["db_stem"] or "").strip(),
            str(row["table_name"] or "").strip(),
        )
        if not all(key):
            continue
        out[key] = int(row["max_local_id"] or 0)
    return out


def _upsert_cursor(
    conn: sqlite3.Connection,
    *,
    account: str,
    username: str,
    db_stem: str,
    table_name: str,
    max_local_id: int,
) -> None:
    conn.execute(
        """
        INSERT INTO monitor_cursors(account, username, db_stem, table_name, max_local_id, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(account, username, db_stem, table_name)
        DO UPDATE SET max_local_id = max(monitor_cursors.max_local_id, excluded.max_local_id),
                      updated_at = excluded.updated_at
        """,
        (account, username, db_stem, table_name, int(max_local_id), _now_ms()),
    )


def build_monitor_text(hit: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("content", "title", "url", "quoteTitle", "quoteContent", "amount"):
        value = re.sub(r"\s+", " ", str(hit.get(key) or "").strip())
        if value and value not in parts:
            parts.append(value)
    text = "\n".join(parts).strip()
    if len(text) > _MAX_STORED_CONTENT_LEN:
        return text[:_MAX_STORED_CONTENT_LEN]
    return text


def match_keywords(text: str, keywords: list[str]) -> list[str]:
    haystack = str(text or "").casefold()
    if not haystack:
        return []
    return [kw for kw in keywords if str(kw or "").casefold() in haystack]


def _is_filtered(text: str, filter_keywords: list[str]) -> bool:
    return bool(match_keywords(text, filter_keywords))


def _sender_display_name(account_dir: Path, sender_username: str) -> str:
    sender = str(sender_username or "").strip()
    if not sender:
        return ""
    if sender == account_dir.name:
        return "我"
    try:
        rows = _load_contact_rows(account_dir / "contact.db", [sender])
        return _pick_display_name(rows.get(sender), sender)
    except Exception:
        return sender


def _insert_hit(
    conn: sqlite3.Connection,
    *,
    account_dir: Path,
    hit: dict[str, Any],
    conversation_name: str,
    text: str,
    matched_keywords: list[str],
    sender_name_cache: Optional[dict[str, str]] = None,
) -> bool:
    message_id = str(hit.get("id") or "").strip()
    parts = message_id.split(":", 2)
    if len(parts) != 3:
        return False
    db_stem, table_name, local_id_s = parts
    try:
        local_id = int(local_id_s)
    except Exception:
        return False
    if not db_stem or not table_name or local_id <= 0:
        return False

    before = conn.total_changes
    sender_username = str(hit.get("senderUsername") or "").strip()
    if sender_name_cache is not None:
        if sender_username not in sender_name_cache:
            sender_name_cache[sender_username] = _sender_display_name(account_dir, sender_username)
        sender_display_name = sender_name_cache.get(sender_username, "")
    else:
        sender_display_name = _sender_display_name(account_dir, sender_username)
    conn.execute(
        """
        INSERT OR IGNORE INTO monitor_hits(
            account, username, conversation_name, sender_username, sender_display_name,
            create_time, message_id, db_stem, table_name, local_id, server_id,
            local_type, render_type, content, matched_keywords_json, is_read, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
        """,
        (
            account_dir.name,
            str(hit.get("username") or "").strip(),
            conversation_name,
            sender_username,
            sender_display_name,
            int(hit.get("createTime") or 0),
            message_id,
            db_stem,
            table_name,
            int(local_id),
            int(hit.get("serverId") or 0),
            int(hit.get("type") or 0),
            str(hit.get("renderType") or "").strip(),
            text,
            _dumps_list(matched_keywords),
            _now_ms(),
        ),
    )
    return conn.total_changes > before


def process_account(account_dir: Path, *, max_rows_per_table: int = 1000) -> dict[str, Any]:
    account = account_dir.name
    if max_rows_per_table <= 0:
        max_rows_per_table = 1000
    if max_rows_per_table > 5000:
        max_rows_per_table = 5000

    with _LOCK:
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = _connect()
            settings_row = conn.execute(
                "SELECT * FROM monitor_settings WHERE account = ? LIMIT 1",
                (account,),
            ).fetchone()
            settings = _row_to_settings(settings_row, account)
            if not settings["enabled"]:
                return {"status": "skipped", "account": account, "reason": "disabled", "inserted": 0}

            monitor_keywords = normalize_keywords(settings.get("monitorKeywords") or [])
            filter_keywords = normalize_keywords(settings.get("filterKeywords") or [])
            if not monitor_keywords:
                return {"status": "skipped", "account": account, "reason": "no_keywords", "inserted": 0}

            if not _has_cursors(conn, account):
                baseline_tables = _initialize_account_baseline(conn, account_dir)
                conn.commit()
                return {
                    "status": "success",
                    "account": account,
                    "baselineCreated": True,
                    "baselineTables": int(baseline_tables),
                    "scanned": 0,
                    "inserted": 0,
                }

            sessions = _load_sessions(account_dir)
            excluded_groups = {
                str(item.get("username") or "").strip()
                for item in normalize_excluded_groups(settings.get("excludedGroups") or [])
                if str(item.get("username") or "").strip()
            }
            cursors = _load_cursors(conn, account)
            scanned = 0
            inserted = 0
            matched = 0
            filtered = 0
            skipped_groups = 0
            sender_name_cache: dict[str, str] = {}

            for db_path in _iter_message_db_paths(account_dir):
                msg_conn: Optional[sqlite3.Connection] = None
                try:
                    msg_conn = sqlite3.connect(str(db_path))
                    msg_conn.row_factory = sqlite3.Row
                    table_rows = msg_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                    names = [str(row[0] or "").strip() for row in table_rows if row and row[0]]
                    lower_to_actual = {name.lower(): name for name in names if name}
                    try:
                        my_row = msg_conn.execute(
                            "SELECT rowid FROM Name2Id WHERE user_name = ? LIMIT 1",
                            (account,),
                        ).fetchone()
                        my_rowid = int(my_row[0]) if my_row is not None and my_row[0] is not None else None
                    except Exception:
                        my_rowid = None

                    msg_conn.text_factory = bytes
                    for username, info in sessions.items():
                        table_name = _resolve_msg_table_name_by_map(lower_to_actual, username)
                        if not table_name:
                            continue
                        cursor_key = (username, db_path.stem, table_name)
                        cursor_local_id = int(cursors.get(cursor_key, 0) or 0)
                        quoted_table = _quote_ident(table_name)
                        sql_with_join = (
                            "SELECT "
                            "m.local_id, m.server_id, m.local_type, m.sort_seq, m.real_sender_id, m.create_time, "
                            "m.message_content, m.compress_content, n.user_name AS sender_username "
                            f"FROM {quoted_table} m "
                            "LEFT JOIN Name2Id n ON m.real_sender_id = n.rowid "
                            "WHERE m.local_id > ? "
                            "ORDER BY m.local_id ASC "
                            "LIMIT ?"
                        )
                        sql_no_join = (
                            "SELECT "
                            "m.local_id, m.server_id, m.local_type, m.sort_seq, m.real_sender_id, m.create_time, "
                            "m.message_content, m.compress_content, '' AS sender_username "
                            f"FROM {quoted_table} m "
                            "WHERE m.local_id > ? "
                            "ORDER BY m.local_id ASC "
                            "LIMIT ?"
                        )
                        try:
                            try:
                                rows = msg_conn.execute(sql_with_join, (cursor_local_id, int(max_rows_per_table))).fetchall()
                            except Exception:
                                rows = msg_conn.execute(sql_no_join, (cursor_local_id, int(max_rows_per_table))).fetchall()
                        except Exception:
                            continue
                        if not rows:
                            continue

                        max_seen = cursor_local_id
                        for row in rows:
                            try:
                                local_id = int(row["local_id"] or 0)
                            except Exception:
                                local_id = 0
                            if local_id > max_seen:
                                max_seen = local_id
                            scanned += 1

                            if bool(info.get("isGroup")) and username in excluded_groups:
                                skipped_groups += 1
                                continue

                            try:
                                hit = _row_to_search_hit(
                                    row,
                                    db_path=db_path,
                                    table_name=table_name,
                                    username=username,
                                    account_dir=account_dir,
                                    is_group=bool(info.get("isGroup")),
                                    my_rowid=my_rowid,
                                )
                            except Exception:
                                continue

                            text = build_monitor_text(hit)
                            if not text:
                                continue
                            hit_keywords = match_keywords(text, monitor_keywords)
                            if not hit_keywords:
                                continue
                            matched += 1
                            if _is_filtered(text, filter_keywords):
                                filtered += 1
                                continue
                            if _insert_hit(
                                conn,
                                account_dir=account_dir,
                                hit=hit,
                                conversation_name=str(info.get("name") or username),
                                text=text,
                                matched_keywords=hit_keywords,
                                sender_name_cache=sender_name_cache,
                            ):
                                inserted += 1

                        _upsert_cursor(
                            conn,
                            account=account,
                            username=username,
                            db_stem=db_path.stem,
                            table_name=table_name,
                            max_local_id=max_seen,
                        )
                except Exception:
                    logger.exception("[keyword-monitor] process db failed account=%s db=%s", account, str(db_path))
                    continue
                finally:
                    if msg_conn is not None:
                        msg_conn.close()

            conn.commit()
            return {
                "status": "success",
                "account": account,
                "baselineCreated": False,
                "scanned": int(scanned),
                "matched": int(matched),
                "filtered": int(filtered),
                "skippedGroups": int(skipped_groups),
                "inserted": int(inserted),
            }
        finally:
            if conn is not None:
                conn.close()


def _row_to_hit(row: sqlite3.Row) -> dict[str, Any]:
    matched_keywords = normalize_keywords(_loads_list(row["matched_keywords_json"]))
    return {
        "id": int(row["id"] or 0),
        "account": str(row["account"] or ""),
        "username": str(row["username"] or ""),
        "conversationName": str(row["conversation_name"] or ""),
        "senderUsername": str(row["sender_username"] or ""),
        "senderDisplayName": str(row["sender_display_name"] or ""),
        "createTime": int(row["create_time"] or 0),
        "messageId": str(row["message_id"] or ""),
        "dbStem": str(row["db_stem"] or ""),
        "tableName": str(row["table_name"] or ""),
        "localId": int(row["local_id"] or 0),
        "serverId": int(row["server_id"] or 0),
        "type": int(row["local_type"] or 0),
        "renderType": str(row["render_type"] or ""),
        "content": str(row["content"] or ""),
        "matchedKeywords": matched_keywords,
        "isRead": bool(int(row["is_read"] or 0)),
        "readAt": int(row["read_at"] or 0) if row["read_at"] is not None else None,
        "createdAt": int(row["created_at"] or 0),
    }


def list_hits(account: str, *, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    account_name = str(account or "").strip()
    if limit <= 0:
        limit = 50
    if limit > 200:
        limit = 200
    if offset < 0:
        offset = 0
    with _LOCK:
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = _connect()
            total_row = conn.execute(
                "SELECT COUNT(1) AS c FROM monitor_hits WHERE account = ?",
                (account_name,),
            ).fetchone()
            total = int(total_row["c"] or 0) if total_row is not None else 0
            rows = conn.execute(
                """
                SELECT *
                FROM monitor_hits
                WHERE account = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (account_name, int(limit), int(offset)),
            ).fetchall()
            return {
                "status": "success",
                "account": account_name,
                "total": int(total),
                "limit": int(limit),
                "offset": int(offset),
                "hasMore": int(offset) + int(limit) < int(total),
                "hits": [_row_to_hit(row) for row in rows],
            }
        finally:
            if conn is not None:
                conn.close()


def get_summary(account: str) -> dict[str, Any]:
    account_name = str(account or "").strip()
    settings = get_settings(account_name)
    with _LOCK:
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = _connect()
            total_row = conn.execute(
                "SELECT COUNT(1) AS c FROM monitor_hits WHERE account = ?",
                (account_name,),
            ).fetchone()
            unread_row = conn.execute(
                "SELECT COUNT(1) AS c FROM monitor_hits WHERE account = ? AND is_read = 0",
                (account_name,),
            ).fetchone()
            last_row = conn.execute(
                "SELECT MAX(created_at) AS last_at FROM monitor_hits WHERE account = ?",
                (account_name,),
            ).fetchone()
            return {
                "status": "success",
                "account": account_name,
                "enabled": bool(settings.get("enabled")),
                "total": int(total_row["c"] or 0) if total_row is not None else 0,
                "unread": int(unread_row["c"] or 0) if unread_row is not None else 0,
                "lastHitAt": int(last_row["last_at"] or 0) if last_row is not None else 0,
            }
        finally:
            if conn is not None:
                conn.close()


def mark_hits_read(account: str, hit_ids: Optional[list[int]] = None) -> dict[str, Any]:
    account_name = str(account or "").strip()
    ids: list[int] = []
    for item in hit_ids or []:
        try:
            value = int(item or 0)
        except Exception:
            continue
        if value > 0:
            ids.append(value)
    now = _now_ms()
    with _LOCK:
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = _connect()
            before = conn.total_changes
            if ids:
                placeholders = ",".join(["?"] * len(ids))
                conn.execute(
                    f"""
                    UPDATE monitor_hits
                    SET is_read = 1, read_at = ?
                    WHERE account = ? AND id IN ({placeholders}) AND is_read = 0
                    """,
                    [now, account_name, *ids],
                )
            else:
                conn.execute(
                    "UPDATE monitor_hits SET is_read = 1, read_at = ? WHERE account = ? AND is_read = 0",
                    (now, account_name),
                )
            conn.commit()
            return {
                "status": "success",
                "account": account_name,
                "updated": int(conn.total_changes - before),
            }
        finally:
            if conn is not None:
                conn.close()


def delete_account_monitor_data(account: str) -> int:
    account_name = str(account or "").strip()
    if not account_name:
        return 0
    with _LOCK:
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = _connect()
            before = conn.total_changes
            conn.execute("DELETE FROM monitor_hits WHERE account = ?", (account_name,))
            conn.execute("DELETE FROM monitor_cursors WHERE account = ?", (account_name,))
            conn.execute("DELETE FROM monitor_settings WHERE account = ?", (account_name,))
            conn.commit()
            return int(conn.total_changes - before)
        except Exception:
            return 0
        finally:
            if conn is not None:
                conn.close()
