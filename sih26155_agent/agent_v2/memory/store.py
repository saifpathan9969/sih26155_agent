"""
Memory — SQLite Persistent Store
GAACA v2.0

Backs all memory subsystems with durable SQLite storage.
Provides save/load for:
- Episodic memory (episodes)
- Semantic memory (concepts, facts)
- Procedural memory (knowledge patterns)
- Agent state snapshots
"""

from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class MemoryStore:
    """SQLite-backed persistent storage for all memory subsystems."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("agent_memory.db")
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _init_db(self):
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")

        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                cycle_index INTEGER NOT NULL,
                objective TEXT,
                action_taken TEXT,
                parameters TEXT,
                observation_summary TEXT,
                success INTEGER,
                surprise INTEGER DEFAULT 0,
                surprise_description TEXT,
                beliefs_added TEXT,
                beliefs_contradicted TEXT,
                hypothesis_formed TEXT,
                correction_applied TEXT,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS concepts (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                attributes TEXT,
                related_concepts TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS facts (
                id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                value TEXT,
                source TEXT,
                confidence REAL DEFAULT 1.0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS knowledge_patterns (
                id TEXT PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                description TEXT,
                content TEXT,
                validation_method TEXT,
                applicability_conditions TEXT,
                source_run_ids TEXT,
                times_applied INTEGER DEFAULT 0,
                times_succeeded INTEGER DEFAULT 0,
                times_failed INTEGER DEFAULT 0,
                contradiction_count INTEGER DEFAULT 0,
                retired INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                last_used TEXT
            );

            CREATE TABLE IF NOT EXISTS state_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                state_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_episodes_run ON episodes(run_id);
            CREATE INDEX IF NOT EXISTS idx_facts_subject ON facts(subject);
            CREATE INDEX IF NOT EXISTS idx_patterns_type ON knowledge_patterns(pattern_type);
        """)
        self._conn.commit()

    # ── Episodes ──────────────────────────────────────────────

    def save_episode(self, episode_data: Dict[str, Any]):
        self._conn.execute(
            """INSERT INTO episodes
               (run_id, cycle_index, objective, action_taken, parameters,
                observation_summary, success, surprise, surprise_description,
                beliefs_added, beliefs_contradicted, hypothesis_formed,
                correction_applied, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                episode_data.get("run_id", ""),
                episode_data.get("cycle_index", 0),
                episode_data.get("objective", ""),
                episode_data.get("action_taken", ""),
                json.dumps(episode_data.get("parameters", {})),
                episode_data.get("observation_summary", ""),
                int(episode_data.get("success", False)),
                int(episode_data.get("surprise", False)),
                episode_data.get("surprise_description"),
                json.dumps(episode_data.get("beliefs_added", [])),
                json.dumps(episode_data.get("beliefs_contradicted", [])),
                episode_data.get("hypothesis_formed"),
                episode_data.get("correction_applied"),
                episode_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            ),
        )
        self._conn.commit()

    def load_episodes(self, run_id: Optional[str] = None) -> List[Dict]:
        if run_id:
            rows = self._conn.execute(
                "SELECT * FROM episodes WHERE run_id=? ORDER BY cycle_index", (run_id,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM episodes ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    # ── Concepts ──────────────────────────────────────────────

    def save_concept(self, concept_data: Dict[str, Any]):
        self._conn.execute(
            """INSERT OR REPLACE INTO concepts
               (id, category, name, description, attributes, related_concepts, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                concept_data["id"],
                concept_data.get("category", ""),
                concept_data.get("name", ""),
                concept_data.get("description", ""),
                json.dumps(concept_data.get("attributes", {})),
                json.dumps(concept_data.get("related_concepts", [])),
                concept_data.get("created_at", datetime.now(timezone.utc).isoformat()),
            ),
        )
        self._conn.commit()

    def load_concepts(self, category: Optional[str] = None) -> List[Dict]:
        if category:
            rows = self._conn.execute(
                "SELECT * FROM concepts WHERE category=?", (category,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM concepts").fetchall()
        return [dict(r) for r in rows]

    # ── Facts ─────────────────────────────────────────────────

    def save_fact(self, fact_data: Dict[str, Any]):
        self._conn.execute(
            """INSERT OR REPLACE INTO facts
               (id, subject, predicate, value, source, confidence, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                fact_data["id"],
                fact_data.get("subject", ""),
                fact_data.get("predicate", ""),
                json.dumps(fact_data.get("value")),
                fact_data.get("source", ""),
                fact_data.get("confidence", 1.0),
                fact_data.get("created_at", datetime.now(timezone.utc).isoformat()),
            ),
        )
        self._conn.commit()

    def load_facts(self, subject: Optional[str] = None) -> List[Dict]:
        if subject:
            rows = self._conn.execute(
                "SELECT * FROM facts WHERE subject=?", (subject,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM facts").fetchall()
        return [dict(r) for r in rows]

    # ── Knowledge Patterns ────────────────────────────────────

    def save_pattern(self, pattern_data: Dict[str, Any]):
        self._conn.execute(
            """INSERT OR REPLACE INTO knowledge_patterns
               (id, pattern_type, description, content, validation_method,
                applicability_conditions, source_run_ids, times_applied,
                times_succeeded, times_failed, contradiction_count, retired,
                created_at, last_used)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                pattern_data["id"],
                pattern_data.get("pattern_type", ""),
                pattern_data.get("description", ""),
                json.dumps(pattern_data.get("content", {})),
                pattern_data.get("validation_method", "UNVALIDATED"),
                json.dumps(pattern_data.get("applicability_conditions", [])),
                json.dumps(pattern_data.get("source_run_ids", [])),
                pattern_data.get("times_applied", 0),
                pattern_data.get("times_succeeded", 0),
                pattern_data.get("times_failed", 0),
                pattern_data.get("contradiction_count", 0),
                int(pattern_data.get("retired", False)),
                pattern_data.get("created_at", datetime.now(timezone.utc).isoformat()),
                pattern_data.get("last_used"),
            ),
        )
        self._conn.commit()

    def load_patterns(self, pattern_type: Optional[str] = None,
                      include_retired: bool = False) -> List[Dict]:
        query = "SELECT * FROM knowledge_patterns"
        conditions = []
        params = []

        if pattern_type:
            conditions.append("pattern_type=?")
            params.append(pattern_type)
        if not include_retired:
            conditions.append("retired=0")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        rows = self._conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    # ── State Snapshots ───────────────────────────────────────

    def save_state_snapshot(self, run_id: str, state_dict: Dict[str, Any]):
        self._conn.execute(
            "INSERT INTO state_snapshots (run_id, state_json, created_at) VALUES (?, ?, ?)",
            (run_id, json.dumps(state_dict, default=str), datetime.now(timezone.utc).isoformat()),
        )
        self._conn.commit()

    def load_latest_snapshot(self, run_id: str) -> Optional[Dict]:
        row = self._conn.execute(
            "SELECT * FROM state_snapshots WHERE run_id=? ORDER BY id DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        if row:
            result = dict(row)
            result["state_json"] = json.loads(result["state_json"])
            return result
        return None

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
