import hashlib
import os
import sqlite3
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import FastAPI
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


ACCOUNT = "wxid_me"
DIRECT_USER = "wxid_friend"
GROUP_USER = "room@chatroom"


def _message_table(username: str) -> str:
    return f"Msg_{hashlib.md5(username.encode('utf-8')).hexdigest()}"


class TestKeywordMonitor(unittest.TestCase):
    def setUp(self):
        self._td = TemporaryDirectory(ignore_cleanup_errors=True)
        self._prev_data_dir = os.environ.get("WECHAT_TOOL_DATA_DIR")
        self._prev_output_dir = os.environ.get("WECHAT_TOOL_OUTPUT_DIR")
        os.environ["WECHAT_TOOL_DATA_DIR"] = self._td.name
        os.environ.pop("WECHAT_TOOL_OUTPUT_DIR", None)

        from wechat_decrypt_tool import keyword_monitor

        self.monitor = keyword_monitor
        self.root = Path(self._td.name)
        self.account_dir = self._create_account()

    def tearDown(self):
        if self._prev_data_dir is None:
            os.environ.pop("WECHAT_TOOL_DATA_DIR", None)
        else:
            os.environ["WECHAT_TOOL_DATA_DIR"] = self._prev_data_dir
        if self._prev_output_dir is None:
            os.environ.pop("WECHAT_TOOL_OUTPUT_DIR", None)
        else:
            os.environ["WECHAT_TOOL_OUTPUT_DIR"] = self._prev_output_dir
        self._td.cleanup()

    def _create_account(self) -> Path:
        account_dir = self.root / "output" / "databases" / ACCOUNT
        account_dir.mkdir(parents=True, exist_ok=True)
        self._create_session_db(account_dir)
        self._create_contact_db(account_dir)
        self._create_message_db(account_dir)
        return account_dir

    def _create_session_db(self, account_dir: Path) -> None:
        conn = sqlite3.connect(str(account_dir / "session.db"))
        try:
            conn.execute(
                "CREATE TABLE SessionTable(username TEXT PRIMARY KEY, sort_timestamp INTEGER, last_timestamp INTEGER)"
            )
            conn.executemany(
                "INSERT INTO SessionTable(username, sort_timestamp, last_timestamp) VALUES (?, 0, 0)",
                [(DIRECT_USER,), (GROUP_USER,)],
            )
            conn.commit()
        finally:
            conn.close()

    def _create_contact_db(self, account_dir: Path) -> None:
        ddl = """
            CREATE TABLE {table} (
                username TEXT PRIMARY KEY,
                remark TEXT,
                nick_name TEXT,
                alias TEXT,
                big_head_url TEXT,
                small_head_url TEXT
            )
        """
        conn = sqlite3.connect(str(account_dir / "contact.db"))
        try:
            conn.execute(ddl.format(table="contact"))
            conn.execute(ddl.format(table="stranger"))
            conn.executemany(
                """
                INSERT INTO contact(username, remark, nick_name, alias, big_head_url, small_head_url)
                VALUES (?, ?, ?, '', '', '')
                """,
                [
                    (DIRECT_USER, "好友", "好友昵称"),
                    (GROUP_USER, "项目群", "项目群昵称"),
                    ("wxid_sender", "群成员", "群成员昵称"),
                ],
            )
            conn.commit()
        finally:
            conn.close()

    def _create_message_db(self, account_dir: Path) -> None:
        conn = sqlite3.connect(str(account_dir / "message_0.db"))
        try:
            conn.execute("CREATE TABLE Name2Id(user_name TEXT, is_session INTEGER DEFAULT 1)")
            conn.execute("INSERT INTO Name2Id(rowid, user_name, is_session) VALUES (1, ?, 1)", (ACCOUNT,))
            conn.execute("INSERT INTO Name2Id(rowid, user_name, is_session) VALUES (2, ?, 1)", (DIRECT_USER,))
            conn.execute("INSERT INTO Name2Id(rowid, user_name, is_session) VALUES (3, ?, 1)", ("wxid_sender",))
            for username in (DIRECT_USER, GROUP_USER):
                conn.execute(
                    f"""
                    CREATE TABLE {_message_table(username)} (
                        local_id INTEGER PRIMARY KEY,
                        server_id INTEGER,
                        local_type INTEGER,
                        sort_seq INTEGER,
                        real_sender_id INTEGER,
                        create_time INTEGER,
                        message_content TEXT,
                        compress_content BLOB
                    )
                    """
                )
            conn.commit()
        finally:
            conn.close()

    def _insert_message(self, username: str, local_id: int, content: str, *, sender_rowid: int = 2) -> None:
        conn = sqlite3.connect(str(self.account_dir / "message_0.db"))
        try:
            conn.execute(
                f"""
                INSERT INTO {_message_table(username)}(
                    local_id, server_id, local_type, sort_seq, real_sender_id, create_time,
                    message_content, compress_content
                ) VALUES (?, ?, 1, ?, ?, ?, ?, NULL)
                """,
                (
                    int(local_id),
                    1000 + int(local_id),
                    int(local_id),
                    int(sender_rowid),
                    1_700_000_000 + int(local_id),
                    content,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def _enable_monitor(self, **overrides):
        payload = {
            "enabled": True,
            "monitorKeywords": ["alpha"],
            "filterKeywords": [],
            "excludedGroups": [],
        }
        payload.update(overrides)
        return self.monitor.save_settings(self.account_dir, payload)

    def test_keyword_split_and_case_insensitive_contains(self):
        keywords = self.monitor.normalize_keywords("Alpha, beta\nAlpha；")
        self.assertEqual(keywords, ["Alpha", "beta"])
        self.assertEqual(self.monitor.match_keywords("hello ALPHA", ["alpha", "missing"]), ["alpha"])

    def test_first_enable_creates_baseline_then_processes_only_new_rows(self):
        self._insert_message(DIRECT_USER, 1, "alpha old")

        saved = self._enable_monitor()
        self.assertGreaterEqual(saved.get("baselineTables", 0), 1)

        first = self.monitor.process_account(self.account_dir)
        self.assertEqual(first.get("inserted"), 0)
        self.assertEqual(self.monitor.list_hits(ACCOUNT)["total"], 0)

        self._insert_message(DIRECT_USER, 2, "new Alpha message")
        second = self.monitor.process_account(self.account_dir)
        self.assertEqual(second.get("inserted"), 1)

        hits = self.monitor.list_hits(ACCOUNT)
        self.assertEqual(hits["total"], 1)
        hit = hits["hits"][0]
        self.assertEqual(hit["username"], DIRECT_USER)
        self.assertIn("new Alpha message", hit["content"])
        self.assertEqual(hit["messageId"], f"message_0:{_message_table(DIRECT_USER)}:2")

        third = self.monitor.process_account(self.account_dir)
        self.assertEqual(third.get("inserted"), 0)
        self.assertEqual(self.monitor.list_hits(ACCOUNT)["total"], 1)

    def test_excluded_group_is_filtered_before_keyword_match(self):
        self._enable_monitor(excludedGroups=[{"username": GROUP_USER, "name": "项目群"}])
        self._insert_message(GROUP_USER, 1, "alpha in group", sender_rowid=3)

        result = self.monitor.process_account(self.account_dir)
        self.assertEqual(result.get("inserted"), 0)
        self.assertEqual(result.get("matched"), 0)
        self.assertEqual(result.get("skippedGroups"), 1)
        self.assertEqual(self.monitor.list_hits(ACCOUNT)["total"], 0)

    def test_filter_keyword_applies_after_monitor_keyword_match(self):
        self._enable_monitor(filterKeywords=["ignore"])
        self._insert_message(DIRECT_USER, 1, "alpha but ignore this")

        result = self.monitor.process_account(self.account_dir)
        self.assertEqual(result.get("matched"), 1)
        self.assertEqual(result.get("filtered"), 1)
        self.assertEqual(result.get("inserted"), 0)
        self.assertEqual(self.monitor.list_hits(ACCOUNT)["total"], 0)

    def test_api_settings_groups_hits_summary_and_mark_read(self):
        from wechat_decrypt_tool.routers import keyword_monitor as router_mod

        original_resolver = router_mod._resolve_account_dir
        router_mod._resolve_account_dir = lambda account=None: self.account_dir
        try:
            app = FastAPI()
            app.include_router(router_mod.router)
            client = TestClient(app)

            settings = client.get("/api/keyword-monitor/settings", params={"account": ACCOUNT})
            self.assertEqual(settings.status_code, 200)
            self.assertFalse(settings.json()["enabled"])

            saved = client.put(
                "/api/keyword-monitor/settings",
                json={
                    "account": ACCOUNT,
                    "enabled": True,
                    "monitorKeywords": ["alpha"],
                    "filterKeywords": [],
                    "excludedGroups": [],
                },
            )
            self.assertEqual(saved.status_code, 200)
            self.assertTrue(saved.json()["enabled"])

            groups = client.get("/api/keyword-monitor/groups", params={"account": ACCOUNT})
            self.assertEqual(groups.status_code, 200)
            self.assertEqual(groups.json()["groups"][0]["username"], GROUP_USER)

            self._insert_message(DIRECT_USER, 1, "alpha api hit")
            processed = client.post("/api/keyword-monitor/process", params={"account": ACCOUNT})
            self.assertEqual(processed.status_code, 200)
            self.assertEqual(processed.json()["inserted"], 1)

            hits = client.get("/api/keyword-monitor/hits", params={"account": ACCOUNT, "limit": 50, "offset": 0})
            self.assertEqual(hits.status_code, 200)
            self.assertEqual(hits.json()["total"], 1)
            hit_id = hits.json()["hits"][0]["id"]

            summary = client.get("/api/keyword-monitor/summary", params={"account": ACCOUNT})
            self.assertEqual(summary.status_code, 200)
            self.assertEqual(summary.json()["unread"], 1)

            marked = client.post("/api/keyword-monitor/hits/read", json={"account": ACCOUNT, "hitIds": [hit_id]})
            self.assertEqual(marked.status_code, 200)
            self.assertEqual(marked.json()["updated"], 1)

            summary_after = client.get("/api/keyword-monitor/summary", params={"account": ACCOUNT})
            self.assertEqual(summary_after.json()["unread"], 0)
        finally:
            router_mod._resolve_account_dir = original_resolver


if __name__ == "__main__":
    unittest.main()
