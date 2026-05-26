"""
storage.py
All data stored on npoint.io — no local JSON files.
"""

import time
import requests
from config import NPOINT_HONOR_URL, NPOINT_STONE_URL, NPOINT_BLOCKED_URL

COOLDOWN_SECONDS = 4 * 60 * 60  # 4 hours


# ── Generic helpers ───────────────────────────────────────────────────────────
def _get(url: str) -> dict:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def _post(url: str, data: dict):
    r = requests.post(url, json=data, timeout=10)
    r.raise_for_status()


# ── DM blocked users ──────────────────────────────────────────────────────────
def load_blocked_users() -> set:
    try:
        data = _get(NPOINT_BLOCKED_URL)
        return set(data["blocked"])
    except Exception:
        return set()

def save_blocked_users(blocked_users: set):
    _post(NPOINT_BLOCKED_URL, {"blocked": list(blocked_users)})


# ── Stone leaderboard ─────────────────────────────────────────────────────────
def load_stone_data() -> dict:
    try:
        data = _get(NPOINT_STONE_URL)
        return data["scores"]
    except Exception:
        return {}

def save_stone_data(scores: dict):
    _post(NPOINT_STONE_URL, {"scores": scores})


# ── Honor/karma system ────────────────────────────────────────────────────────
def _ensure_user(data: dict, uid: str):
    if uid not in data["users"]:
        data["users"][uid] = {"karma": 0, "cooldowns": {}}

def get_honor_user(user_id: int) -> dict | None:
    data = _get(NPOINT_HONOR_URL)
    return data["users"].get(str(user_id))

def add_honor(target_id: int, voter_id: int) -> tuple[bool, str]:
    data = _get(NPOINT_HONOR_URL)
    tid, vid = str(target_id), str(voter_id)

    if tid == vid:
        return False, "You can't rep yourself."

    _ensure_user(data, tid)

    last = data["users"][tid]["cooldowns"].get(vid, 0)
    remaining = COOLDOWN_SECONDS - (time.time() - last)
    if remaining > 0:
        hours   = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        return False, f"You can +rep this user again in **{hours}h {minutes}m**."

    data["users"][tid]["karma"] += 1
    data["users"][tid]["cooldowns"][vid] = time.time()
    _post(NPOINT_HONOR_URL, data)
    return True, f" +rep They now have **{data['users'][tid]['karma']}** karma :mandylove:"

def remove_honor(target_id: int, voter_id: int) -> tuple[bool, str]:
    data = _get(NPOINT_HONOR_URL)
    tid, vid = str(target_id), str(voter_id)

    if tid == vid:
        return False, "You can't rep yourself."

    _ensure_user(data, tid)

    last = data["users"][tid]["cooldowns"].get(vid, 0)
    remaining = COOLDOWN_SECONDS - (time.time() - last)
    if remaining > 0:
        hours   = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        return False, f"You can -rep this user again in **{hours}h {minutes}m**."

    data["users"][tid]["karma"] -= 1
    data["users"][tid]["cooldowns"][vid] = time.time()
    _post(NPOINT_HONOR_URL, data)
    return True, f"👎 -rep. That fool now has **{data['users'][tid]['karma']}** rep :KILL:"

def get_honor_leaderboard(top_n: int = 10) -> list[tuple[str, int]]:
    data = _get(NPOINT_HONOR_URL)
    sorted_users = sorted(
        data["users"].items(),
        key=lambda x: x[1]["karma"],
        reverse=True
    )
    return [(uid, info["karma"]) for uid, info in sorted_users[:top_n]]
