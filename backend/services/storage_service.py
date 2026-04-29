"""SQLite persistence for approved cases and audit events."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


DB_PATH = Path(__file__).resolve().parents[1] / "nyayasetu.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS approved_cases (
                job_id TEXT PRIMARY KEY,
                extracted_data TEXT NOT NULL,
                action_plan TEXT NOT NULL,
                source_evidence TEXT NOT NULL DEFAULT '{}',
                review_meta TEXT NOT NULL DEFAULT '{}',
                kanban_status TEXT NOT NULL,
                verified_by TEXT NOT NULL DEFAULT 'Demo Reviewer',
                verified_role TEXT NOT NULL DEFAULT 'legal_reviewer',
                approved_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(approved_cases)").fetchall()
        }
        if "verified_role" not in columns:
            conn.execute("ALTER TABLE approved_cases ADD COLUMN verified_role TEXT NOT NULL DEFAULT 'legal_reviewer'")
        if "review_meta" not in columns:
            conn.execute("ALTER TABLE approved_cases ADD COLUMN review_meta TEXT NOT NULL DEFAULT '{}'")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL,
                details TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def add_audit_event(job_id: str, event_type: str, actor: str, details: dict[str, Any]) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO audit_events (job_id, event_type, actor, details, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (job_id, event_type, actor, json.dumps(details), _now()),
        )


def save_approved_case(
    job_id: str,
    extracted_data: dict[str, Any],
    action_plan: dict[str, Any],
    source_evidence: dict[str, Any],
    review_meta: dict[str, Any],
    verified_by: str,
    verified_role: str,
    edits: dict[str, Any],
) -> None:
    init_db()
    timestamp = _now()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO approved_cases (
                job_id, extracted_data, action_plan, source_evidence, review_meta,
                kanban_status, verified_by, verified_role, approved_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                extracted_data=excluded.extracted_data,
                action_plan=excluded.action_plan,
                source_evidence=excluded.source_evidence,
                review_meta=excluded.review_meta,
                verified_by=excluded.verified_by,
                verified_role=excluded.verified_role,
                updated_at=excluded.updated_at
            """,
            (
                job_id,
                json.dumps(extracted_data),
                json.dumps(action_plan),
                json.dumps(source_evidence),
                json.dumps(review_meta),
                "pending_verification",
                verified_by,
                verified_role,
                timestamp,
                timestamp,
            ),
        )

    add_audit_event(
        job_id,
        "approved",
        verified_by,
        {"message": "Case approved for dashboard", "role": verified_role, "edits": edits},
    )


def list_cases() -> list[dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT job_id, extracted_data, action_plan, source_evidence,
                   kanban_status, verified_by, verified_role, approved_at, updated_at, review_meta
            FROM approved_cases
            ORDER BY updated_at DESC
            """
        ).fetchall()

    return [_row_to_case(row) for row in rows]


def get_case(job_id: str) -> dict[str, Any] | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT job_id, extracted_data, action_plan, source_evidence,
                   kanban_status, verified_by, verified_role, approved_at, updated_at, review_meta
            FROM approved_cases
            WHERE job_id = ?
            """,
            (job_id,),
        ).fetchone()
    return _row_to_case(row) if row else None


def update_case_status(job_id: str, status: str, actor: str = "Demo Reviewer") -> bool:
    init_db()
    timestamp = _now()
    with _connect() as conn:
        row = conn.execute(
            "SELECT kanban_status FROM approved_cases WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        if row is None:
            return False
        previous = row["kanban_status"]
        conn.execute(
            "UPDATE approved_cases SET kanban_status = ?, updated_at = ? WHERE job_id = ?",
            (status, timestamp, job_id),
        )

    add_audit_event(
        job_id,
        "status_changed",
        actor,
        {"from": previous, "to": status},
    )
    return True


def get_audit_events(job_id: str) -> list[dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT event_type, actor, details, created_at
            FROM audit_events
            WHERE job_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (job_id,),
        ).fetchall()

    return [
        {
            "event_type": row["event_type"],
            "actor": row["actor"],
            "details": json.loads(row["details"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def _row_to_case(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "job_id": row["job_id"],
        "extracted_data": json.loads(row["extracted_data"]),
        "action_plan": json.loads(row["action_plan"]),
        "source_evidence": json.loads(row["source_evidence"]),
        "review_meta": json.loads(row["review_meta"]),
        "kanban_status": row["kanban_status"],
        "verified_by": row["verified_by"],
        "verified_role": row["verified_role"],
        "approved_at": row["approved_at"],
        "updated_at": row["updated_at"],
    }
