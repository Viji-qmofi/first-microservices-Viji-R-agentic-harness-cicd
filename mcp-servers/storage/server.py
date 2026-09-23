from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

try:
    from fastmcp.exceptions import ToolError
except ImportError:
    class ToolError(Exception):
        pass

DB_PATH = os.getenv("STORAGE_DB_PATH", "/memory/storage.db")
AUDIT_PATH = os.getenv("STORAGE_AUDIT_PATH", "/memory/storage-audit.log")
ALLOW_LIST_PATH = Path(__file__).parent / "allow-list.json"
ALLOW_LIST = json.loads(ALLOW_LIST_PATH.read_text(encoding="utf-8"))

ALLOWED_CLASSIFICATIONS = {"public", "internal", "confidential", "secret"}
WRITE_CLASSIFICATIONS = {"public", "internal"}
PROJECT_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")

mcp = FastMCP("storage")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_db() -> sqlite3.Connection:
    """Open the persistent SQLite database and ensure its schema exists."""
    ensure_parent(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            entry_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            entry_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            classification TEXT NOT NULL,
            deleted INTEGER NOT NULL DEFAULT 0,
            last_updated TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_entries_project_type "
        "ON entries(project_id, entry_type, deleted)"
    )
    return conn


def audit(
    operation: str,
    project_id: str | None,
    entry_id: str | None,
    classification: str | None,
    calling_role: str | None,
    outcome: str = "success",
) -> None:
    """Append one JSON audit record. Agents have no tool that edits this file."""
    ensure_parent(AUDIT_PATH)
    record: dict[str, Any] = {
        "timestamp": utc_now(),
        "operation": operation,
        "project_id": project_id,
        "entry_id": entry_id,
        "classification": classification,
        "calling_role": calling_role or "unknown",
        "outcome": outcome,
    }
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def _authorize(operation: str, calling_role: str, project_id: str | None = None) -> None:
    """Deny-by-default role check against allow-list.json.

    Checks the calling_role the agent declares for itself, the same
    self-declared signal coursetools' role checks have always used -- not
    an environment-variable-based process identity. This project's roles
    run as subagents sharing one Orchestrator container rather than each
    getting a separate container/process, so a container-level identity
    would be identical for every subagent and could not distinguish them.
    See docs/governance-policy.md for the full reasoning. This still
    closes a real gap: previously calling_role was accepted and logged
    but never checked against anything at all.
    """
    allowed_roles = ALLOW_LIST.get(operation, [])
    if calling_role not in allowed_roles:
        audit(operation, project_id, None, None, calling_role, outcome="authorization_denied")
        raise ToolError(
            f"authorization_denied: role '{calling_role}' is not on the allow-list for "
            f"{operation}. Allowed roles: {allowed_roles or 'none'}. "
            f"See docs/governance-policy.md."
        )


def validate_project_id(project_id: str) -> None:
    if not PROJECT_ID_PATTERN.match(project_id or ""):
        raise ValueError("project_id must contain only letters, numbers, and hyphens")


def validate_nonempty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def validate_classification(classification: str) -> None:
    if classification not in ALLOWED_CLASSIFICATIONS:
        raise ValueError(
            f"classification must be one of {sorted(ALLOWED_CLASSIFICATIONS)}"
        )
    if classification not in WRITE_CLASSIFICATIONS:
        raise ValueError(
            "this server does not accept writes classified confidential or secret"
        )


def get_live_entry(conn: sqlite3.Connection, project_id: str, entry_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM entries WHERE project_id = ? AND entry_id = ? AND deleted = 0",
        (project_id, entry_id),
    ).fetchone()


@mcp.tool
def write_entry(
    project_id: str,
    entry_type: str,
    title: str,
    content: str,
    classification: str,
    calling_role: str = "unknown",
) -> dict:
    """Write a new entry to the store. Requires a valid classification tag."""
    _authorize("write_entry", calling_role, project_id)
    validate_project_id(project_id)
    validate_nonempty(entry_type, "entry_type")
    validate_nonempty(title, "title")
    validate_nonempty(content, "content")
    validate_classification(classification)

    entry_id = str(uuid.uuid4())
    now = utc_now()
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO entries (entry_id, project_id, entry_type, title, content, "
            "classification, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (entry_id, project_id, entry_type, title, content, classification, now),
        )
        conn.commit()
    finally:
        conn.close()

    audit("write_entry", project_id, entry_id, classification, calling_role)
    return {"entry_id": entry_id}


@mcp.tool
def read_entry(project_id: str, entry_id: str, calling_role: str = "unknown") -> dict:
    """Read a single entry by ID, scoped to its project."""
    _authorize("read_entry", calling_role, project_id)
    validate_project_id(project_id)
    validate_nonempty(entry_id, "entry_id")

    conn = get_db()
    try:
        row = get_live_entry(conn, project_id, entry_id)
    finally:
        conn.close()

    if row is None:
        raise ValueError("no entry found for that project_id and entry_id")

    audit("read_entry", project_id, entry_id, row["classification"], calling_role)
    return dict(row)


@mcp.tool
def list_entries(project_id: str, entry_type: str | None = None, calling_role: str = "unknown") -> list[dict]:
    """List entries for a project. Metadata only; never returns full content."""
    _authorize("list_entries", calling_role, project_id)
    validate_project_id(project_id)

    conn = get_db()
    try:
        if entry_type is None:
            rows = conn.execute(
                "SELECT entry_id, title, entry_type, classification, last_updated "
                "FROM entries WHERE project_id = ? AND deleted = 0 "
                "ORDER BY last_updated DESC",
                (project_id,),
            ).fetchall()
        else:
            validate_nonempty(entry_type, "entry_type")
            rows = conn.execute(
                "SELECT entry_id, title, entry_type, classification, last_updated "
                "FROM entries WHERE project_id = ? AND entry_type = ? AND deleted = 0 "
                "ORDER BY last_updated DESC",
                (project_id, entry_type),
            ).fetchall()
    finally:
        conn.close()

    audit("list_entries", project_id, None, None, calling_role)
    return [dict(row) for row in rows]


@mcp.tool
def update_entry(
    project_id: str,
    entry_id: str,
    content: str,
    calling_role: str = "unknown",
) -> dict:
    """Update the content of an existing entry. Classification is preserved."""
    _authorize("update_entry", calling_role, project_id)
    validate_project_id(project_id)
    validate_nonempty(entry_id, "entry_id")
    validate_nonempty(content, "content")

    now = utc_now()
    conn = get_db()
    try:
        row = get_live_entry(conn, project_id, entry_id)
        if row is None:
            raise ValueError("no entry found to update")
        conn.execute(
            "UPDATE entries SET content = ?, last_updated = ? "
            "WHERE project_id = ? AND entry_id = ? AND deleted = 0",
            (content, now, project_id, entry_id),
        )
        conn.commit()
        classification = row["classification"]
    finally:
        conn.close()

    audit("update_entry", project_id, entry_id, classification, calling_role)
    return {"success": True}


@mcp.tool
def delete_entry(
    project_id: str,
    entry_id: str,
    calling_role: str = "unknown",
) -> dict:
    """Soft-delete an entry. Marks deleted; does not remove backend evidence."""
    _authorize("delete_entry", calling_role, project_id)
    validate_project_id(project_id)
    validate_nonempty(entry_id, "entry_id")

    conn = get_db()
    try:
        row = get_live_entry(conn, project_id, entry_id)
        if row is None:
            raise ValueError("no entry found to delete")
        conn.execute(
            "UPDATE entries SET deleted = 1, last_updated = ? "
            "WHERE project_id = ? AND entry_id = ? AND deleted = 0",
            (utc_now(), project_id, entry_id),
        )
        conn.commit()
        classification = row["classification"]
    finally:
        conn.close()

    audit("delete_entry", project_id, entry_id, classification, calling_role)
    return {"success": True}


@mcp.tool
def audit_read(limit: int = 50, calling_role: str = "unknown") -> dict:
    """Read the tail of the audit log. Granted to orchestrator only."""
    _authorize("audit_read", calling_role)
    ensure_parent(AUDIT_PATH)
    if not Path(AUDIT_PATH).exists():
        return {"entries": []}
    lines = Path(AUDIT_PATH).read_text(encoding="utf-8").splitlines()[-limit:]
    return {"entries": [json.loads(line) for line in lines if line.strip()]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Persistent storage MCP server")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    import uvicorn
    app = mcp.http_app(
        stateless_http=True,
        middleware=[
            Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
        ],
    )
    uvicorn.run(app, host=args.host, port=args.port)
