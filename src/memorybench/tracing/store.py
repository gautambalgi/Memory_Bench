"""SQLite persistence. Every event commits immediately so partial runs remain inspectable."""

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Redactor:
    def __init__(self, secrets: tuple[str, ...] = ()):
        self.secrets = tuple(value for value in secrets if value)

    def clean(self, value):
        if isinstance(value, dict):
            return {
                key: "[redacted]"
                if key.lower() in {"api_key", "authorization", "password", "secret", "access_token"}
                else self.clean(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [self.clean(item) for item in value]
        if isinstance(value, str):
            for secret in self.secrets:
                value = value.replace(secret, "[redacted]")
            return re.sub(r"sk-[A-Za-z0-9_-]{10,}", "[redacted]", value)
        return value


class RunStore:
    def __init__(self, data_dir: Path, secrets: tuple[str, ...] = ()):
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "runs.sqlite3"
        self.redactor = Redactor(secrets)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, started_at TEXT NOT NULL, status TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    run_id TEXT NOT NULL REFERENCES runs(id), seq INTEGER NOT NULL,
                    payload TEXT NOT NULL, PRIMARY KEY (run_id, seq)
                );
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self, task: str, config: dict) -> dict:
        run = self.redactor.clean(
            {
                "schema_version": 1,
                "id": uuid4().hex,
                "task": task,
                "config": config,
                "started_at": utc_now(),
                "finished_at": None,
                "status": "running",
                "answer": "",
                "duration_ms": 0,
            }
        )
        with self.connect() as db:
            db.execute(
                "INSERT INTO runs VALUES (?, ?, ?, ?)",
                (run["id"], run["started_at"], run["status"], json.dumps(run)),
            )
        return run

    def save(self, run: dict):
        with self.connect() as db:
            db.execute(
                "UPDATE runs SET status=?, payload=? WHERE id=?",
                (run["status"], json.dumps(self.redactor.clean(run)), run["id"]),
            )

    def append(self, run_id: str, kind: str, step: int = 0, duration_ms: float = 0, **data) -> dict:
        with self.connect() as db:
            # Serialize sequence allocation with insertion across connections.
            db.execute("BEGIN IMMEDIATE")
            seq = db.execute(
                "SELECT COALESCE(MAX(seq), 0)+1 FROM events WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            event = self.redactor.clean(
                {
                    "seq": seq,
                    "kind": kind,
                    "step": step,
                    "at": utc_now(),
                    "duration_ms": round(duration_ms, 3),
                    "data": data,
                }
            )
            db.execute("INSERT INTO events VALUES (?, ?, ?)", (run_id, seq, json.dumps(event)))
        return event

    def get(self, run_id: str) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT payload FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise KeyError("Run not found.")
            run = json.loads(row[0])
            run["events"] = [
                json.loads(row[0])
                for row in db.execute(
                    "SELECT payload FROM events WHERE run_id=? ORDER BY seq", (run_id,)
                )
            ]
        return run

    def recent(self, limit: int = 100) -> list[dict]:
        with self.connect() as db:
            return [
                json.loads(row[0])
                for row in db.execute(
                    "SELECT payload FROM runs ORDER BY started_at DESC LIMIT ?", (limit,)
                )
            ]
