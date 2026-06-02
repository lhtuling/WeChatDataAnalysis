from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from ..chat_helpers import _resolve_account_dir
from ..keyword_monitor import (
    get_settings,
    get_summary,
    list_groups,
    list_hits,
    mark_hits_read,
    process_account,
    save_settings,
)
from ..path_fix import PathFixRoute

router = APIRouter(route_class=PathFixRoute)


@router.get("/api/keyword-monitor/settings", summary="Get keyword monitor settings")
def keyword_monitor_settings(account: Optional[str] = None):
    account_dir = _resolve_account_dir(account)
    return get_settings(account_dir.name)


@router.put("/api/keyword-monitor/settings", summary="Save keyword monitor settings")
async def keyword_monitor_save_settings(request: Request):
    payload = await request.json()
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid payload.")
    account = str(payload.get("account") or "").strip() or None
    account_dir = _resolve_account_dir(account)
    return save_settings(account_dir, payload)


@router.get("/api/keyword-monitor/groups", summary="List groups for keyword monitor filters")
def keyword_monitor_groups(account: Optional[str] = None):
    account_dir = _resolve_account_dir(account)
    return list_groups(account_dir)


@router.get("/api/keyword-monitor/hits", summary="List keyword monitor hits")
def keyword_monitor_hits(account: Optional[str] = None, limit: int = 50, offset: int = 0):
    account_dir = _resolve_account_dir(account)
    return list_hits(account_dir.name, limit=limit, offset=offset)


@router.get("/api/keyword-monitor/summary", summary="Keyword monitor summary")
def keyword_monitor_summary(account: Optional[str] = None):
    account_dir = _resolve_account_dir(account)
    return get_summary(account_dir.name)


@router.post("/api/keyword-monitor/hits/read", summary="Mark keyword monitor hits as read")
async def keyword_monitor_hits_read(request: Request):
    payload = await request.json()
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid payload.")
    account = str(payload.get("account") or "").strip() or None
    account_dir = _resolve_account_dir(account)
    raw_ids = payload.get("hitIds", payload.get("hit_ids", []))
    hit_ids: list[int] = []
    if isinstance(raw_ids, list):
        for item in raw_ids:
            try:
                value = int(item or 0)
            except Exception:
                continue
            if value > 0:
                hit_ids.append(value)
    return mark_hits_read(account_dir.name, hit_ids or None)


@router.post("/api/keyword-monitor/process", summary="Process new messages for keyword monitor")
def keyword_monitor_process(account: Optional[str] = None):
    account_dir = _resolve_account_dir(account)
    return process_account(account_dir)
