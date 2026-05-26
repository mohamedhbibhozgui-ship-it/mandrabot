"""
storage.py
Handles all data persistence:
  - Local JSON files for stone leaderboard & DM-blocked users
  - npoint.io REST API for the honor system
"""

import os
import json
import requests
from config import NPOINT_URL

# ── File paths ────────────────────────────────────────────────────────────────
DATA_FILE  = "dm_blocked.json"
STONE_FILE = "stone_leaderboard.json"


# ── DM blocked users ──────────────────────────────────────────────────────────
def load_blocked_users() -> set:
    if not os.path.exists(DATA_FILE):
        return set()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_blocked_users(blocked_users: set):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(blocked_users), f)


# ── Stone leaderboard ─────────────────────────────────────────────────────────
def load_stone_data() -> dict:
    if not os.path.exists(STONE_FILE):
        return {}
    try:
        with open(STONE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_stone_data(data: dict):
    with open(STONE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


# ── Honor system (npoint.io) ──────────────────────────────────────────────────
def _read_honor() -> dict:
    """Fetch the full honor JSON from npoint."""
    r = requests.get(NPOINT_URL, timeout=10)
    r.raise_for_status()
    return r.json()

def _write_honor(data: dict):
    """Push updated honor JSON back to npoint."""
    r = requests.post(NPOINT_URL, json=data, timeout=10)
    r.raise_for_status()

def get_honor_user(user_id: int) -> dict | None:
    """Return a single user's honor record, or None if they don't exist yet."""
    data = _read_honor()
    return data["users"].get(str(user_id))

def add_honor(target_id: int, voter_id: int) -> tuple[bool, str]:
    """
    Give honor from voter → target.
    Returns (success, message).
    """
    data = _read_honor()
    tid, vid = str(target_id), str(voter_id)

    if tid == vid:
        return False, "You can't vouch for yourself."

    if tid not in data["users"]:
        data["users"][tid] = {"honor": 0, "vouched_by": []}

    if vid in data["users"][tid]["vouched_by"]:
        return False, "You already vouched for this user."

    data["users"][tid]["honor"] += 1
    data["users"][tid]["vouched_by"].append(vid)
    _write_honor(data)
    return True, "Honor added!"

def remove_honor(target_id: int, voter_id: int) -> tuple[bool, str]:
    """
    Remove previously given honor.
    Returns (success, message).
    """
    data = _read_honor()
    tid, vid = str(target_id), str(voter_id)

    if tid not in data["users"] or vid not in data["users"][tid]["vouched_by"]:
        return False, "You haven't vouched for this user."

    data["users"][tid]["honor"] -= 1
    data["users"][tid]["vouched_by"].remove(vid)
    _write_honor(data)
    return True, "Honor removed."

def get_honor_leaderboard(top_n: int = 10) -> list[tuple[str, int]]:
    """Return a sorted list of (user_id_str, honor_count) tuples."""
    data = _read_honor()
    sorted_users = sorted(
        data["users"].items(),
        key=lambda x: x[1]["honor"],
        reverse=True
    )
    return [(uid, info["honor"]) for uid, info in sorted_users[:top_n]]