"""
SQLite Persistence Layer — SIH26155
====================================
Provides durable local storage that survives server restarts.
Works alongside Firebase: SQLite is always-on local fallback; Firebase is
the optional cloud layer. On startup main.py calls load_* helpers to hydrate
the in-memory dicts from SQLite before any request is served.

Tables
------
users             – user accounts (email, hashed pw, role, org, audience …)
configurations    – uploaded config texts keyed by username + filename
audit_sessions    – serialised missionResult JSON per user with metadata
blockchain_blocks – each BlockchainBlock as JSON, ordered by index
rule_versions     – every RuleVersion dict (all versions, all rules)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# DB file lives next to main.py
_DB_PATH = Path(__file__).resolve().parent / "gaaca_data.db"

# HMAC secret for rule-hash signing — read from env or use a stable fallback
_RULE_SECRET = os.environ.get("GAACA_RULE_SECRET", "ntro-sih26155-rule-integrity-key").encode()


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

@contextmanager
def _conn():
    con = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create all tables if they don't exist yet. Safe to call on every startup."""
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                username    TEXT PRIMARY KEY,
                email       TEXT NOT NULL,
                password    TEXT NOT NULL,
                role        TEXT DEFAULT 'Lead Security Auditor',
                organization TEXT DEFAULT 'NTRO',
                full_name   TEXT DEFAULT '',
                audience    TEXT DEFAULT 'enterprise',
                photo_url   TEXT DEFAULT '',
                auth_provider TEXT DEFAULT 'password',
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS configurations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT NOT NULL,
                filename    TEXT NOT NULL,
                content     TEXT NOT NULL,
                vendor      TEXT DEFAULT '',
                uploaded_at TEXT DEFAULT (datetime('now')),
                UNIQUE(username, filename)
            );

            CREATE TABLE IF NOT EXISTS audit_sessions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                username     TEXT NOT NULL,
                session_name TEXT DEFAULT '',
                goal         TEXT DEFAULT '',
                result_json  TEXT NOT NULL,
                report_sha256 TEXT DEFAULT '',
                device_count INTEGER DEFAULT 0,
                fail_count   INTEGER DEFAULT 0,
                pass_count   INTEGER DEFAULT 0,
                created_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS blockchain_blocks (
                block_index  INTEGER PRIMARY KEY,
                block_json   TEXT NOT NULL,
                created_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS rule_versions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id      TEXT NOT NULL,
                version_num  INTEGER NOT NULL,
                version_json TEXT NOT NULL,
                sha256_hash  TEXT DEFAULT '',
                hmac_sig     TEXT DEFAULT '',
                created_at   TEXT DEFAULT (datetime('now')),
                UNIQUE(rule_id, version_num)
            );
        """)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def save_user(user: dict) -> None:
    uname = (user.get("username") or user.get("email") or "").strip().lower()
    if not uname:
        return
    with _conn() as con:
        con.execute("""
            INSERT INTO users (username, email, password, role, organization, full_name, audience, photo_url, auth_provider)
            VALUES (:u, :e, :p, :r, :o, :f, :a, :ph, :ap)
            ON CONFLICT(username) DO UPDATE SET
                email=excluded.email, password=excluded.password,
                role=excluded.role, organization=excluded.organization,
                full_name=excluded.full_name, audience=excluded.audience,
                photo_url=excluded.photo_url, auth_provider=excluded.auth_provider
        """, {
            "u": uname,
            "e": user.get("email", uname),
            "p": user.get("password", ""),
            "r": user.get("role", "Lead Security Auditor"),
            "o": user.get("organization", "NTRO"),
            "f": user.get("full_name", ""),
            "a": user.get("audience", "enterprise"),
            "ph": user.get("photo_url", ""),
            "ap": user.get("auth_provider", "password"),
        })


def load_all_users() -> List[dict]:
    with _conn() as con:
        rows = con.execute("SELECT * FROM users").fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Configurations
# ---------------------------------------------------------------------------

def save_config(username: str, filename: str, content: str, vendor: str = "") -> None:
    uname = username.strip().lower()
    with _conn() as con:
        con.execute("""
            INSERT INTO configurations (username, filename, content, vendor, uploaded_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(username, filename) DO UPDATE SET
                content=excluded.content, vendor=excluded.vendor,
                uploaded_at=excluded.uploaded_at
        """, (uname, filename, content, vendor, datetime.now(timezone.utc).isoformat()))


def load_configs_for_user(username: str) -> List[dict]:
    uname = username.strip().lower()
    with _conn() as con:
        rows = con.execute(
            "SELECT filename, content, vendor, uploaded_at FROM configurations WHERE username=?",
            (uname,)
        ).fetchall()
    return [dict(r) for r in rows]


def load_all_configs() -> List[dict]:
    """Load every config (all users) — used to rebuild _all_configs on startup."""
    with _conn() as con:
        rows = con.execute(
            "SELECT username, filename, content, vendor, uploaded_at FROM configurations"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_config(username: str, filename: str) -> None:
    uname = username.strip().lower()
    with _conn() as con:
        con.execute(
            "DELETE FROM configurations WHERE username=? AND filename=?",
            (uname, filename)
        )


# ---------------------------------------------------------------------------
# Audit Sessions
# ---------------------------------------------------------------------------

def save_audit_session(
    username: str,
    result: dict,
    goal: str = "",
    session_name: str = "",
) -> int:
    """Persist a mission result. Returns the new row id."""
    uname = username.strip().lower()
    # Compute summary counts
    fbd = result.get("findings_by_device") or {}
    device_count = len(result.get("audited_devices") or list(fbd.keys()))
    pass_count = fail_count = 0
    for findings in fbd.values():
        for f in findings:
            s = (f.get("status") or "").lower()
            if s == "pass":
                pass_count += 1
            elif s == "fail":
                fail_count += 1

    # Strip the full report text from JSON to keep DB small — store separately
    slim = {k: v for k, v in result.items() if k != "report"}
    with _conn() as con:
        cur = con.execute("""
            INSERT INTO audit_sessions
                (username, session_name, goal, result_json, report_sha256, device_count, fail_count, pass_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            uname,
            session_name or f"Audit {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
            goal,
            json.dumps(slim, default=str),
            result.get("report_sha256", ""),
            device_count,
            fail_count,
            pass_count,
        ))
        return cur.lastrowid


def load_sessions_for_user(username: str, limit: int = 20) -> List[dict]:
    uname = username.strip().lower()
    with _conn() as con:
        rows = con.execute("""
            SELECT id, session_name, goal, report_sha256, device_count, fail_count, pass_count, created_at
            FROM audit_sessions WHERE username=?
            ORDER BY created_at DESC LIMIT ?
        """, (uname, limit)).fetchall()
    return [dict(r) for r in rows]


def load_session_by_id(session_id: int) -> Optional[dict]:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM audit_sessions WHERE id=?", (session_id,)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    try:
        d["result"] = json.loads(d.pop("result_json", "{}"))
    except Exception:
        d["result"] = {}
    return d


# ---------------------------------------------------------------------------
# Blockchain Blocks
# ---------------------------------------------------------------------------

def save_block(block_dict: dict) -> None:
    idx = block_dict.get("index", 0)
    with _conn() as con:
        con.execute("""
            INSERT INTO blockchain_blocks (block_index, block_json)
            VALUES (?, ?)
            ON CONFLICT(block_index) DO UPDATE SET block_json=excluded.block_json
        """, (idx, json.dumps(block_dict, default=str)))


def load_all_blocks() -> List[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT block_json FROM blockchain_blocks ORDER BY block_index"
        ).fetchall()
    result = []
    for row in rows:
        try:
            result.append(json.loads(row["block_json"]))
        except Exception:
            pass
    return result


# ---------------------------------------------------------------------------
# Rule Versions  (meaningful hashes via HMAC-SHA256)
# ---------------------------------------------------------------------------

def sign_rule(rule_dict: dict, version: int) -> tuple[str, str]:
    """
    Returns (sha256_hash, hmac_sig).

    sha256_hash  – deterministic digest of the rule's canonical fields.
    hmac_sig     – HMAC-SHA256 over the same canonical JSON using _RULE_SECRET.
                   This makes the hash meaningful: only the server that holds
                   the secret can produce a valid signature. Anyone can verify
                   the rule hasn't changed since signing by recomputing the HMAC.
    """
    canonical = json.dumps({
        "id":                  rule_dict.get("id") or rule_dict.get("rule_id"),
        "version":             version,
        "baseline_field_path": rule_dict.get("baseline_field_path"),
        "evaluation":          rule_dict.get("evaluation"),
        "severity":            rule_dict.get("severity"),
        "framework":           rule_dict.get("framework"),
    }, sort_keys=True)
    sha = hashlib.sha256(canonical.encode()).hexdigest()
    sig = hmac.new(_RULE_SECRET, canonical.encode(), hashlib.sha256).hexdigest()
    return sha, sig


def verify_rule_signature(rule_dict: dict, version: int, expected_hmac: str) -> bool:
    """Return True if the rule's HMAC matches what was recorded at signing time."""
    _, sig = sign_rule(rule_dict, version)
    return hmac.compare_digest(sig, expected_hmac)


def save_rule_version(rule_id: str, version_num: int, version_dict: dict) -> None:
    sha, sig = sign_rule(version_dict.get("rule_data") or version_dict, version_num)
    version_dict = dict(version_dict)
    version_dict["sha256_hash"] = sha
    version_dict["hmac_sig"] = sig
    with _conn() as con:
        con.execute("""
            INSERT INTO rule_versions (rule_id, version_num, version_json, sha256_hash, hmac_sig)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(rule_id, version_num) DO UPDATE SET
                version_json=excluded.version_json,
                sha256_hash=excluded.sha256_hash,
                hmac_sig=excluded.hmac_sig
        """, (rule_id, version_num, json.dumps(version_dict, default=str), sha, sig))


def load_rule_versions(rule_id: str) -> List[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT version_json, hmac_sig FROM rule_versions WHERE rule_id=? ORDER BY version_num",
            (rule_id,)
        ).fetchall()
    result = []
    for row in rows:
        try:
            d = json.loads(row["version_json"])
            d["_db_hmac"] = row["hmac_sig"]
            result.append(d)
        except Exception:
            pass
    return result


def load_all_rule_versions() -> Dict[str, List[dict]]:
    with _conn() as con:
        rows = con.execute(
            "SELECT rule_id, version_num, version_json, hmac_sig FROM rule_versions ORDER BY rule_id, version_num"
        ).fetchall()
    result: Dict[str, List[dict]] = {}
    for row in rows:
        try:
            d = json.loads(row["version_json"])
            d["_db_hmac"] = row["hmac_sig"]
            result.setdefault(row["rule_id"], []).append(d)
        except Exception:
            pass
    return result
