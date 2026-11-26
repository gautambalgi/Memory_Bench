"""Local, per-learner summaries for the Study Assistant."""

import sqlite3
from contextlib import closing, contextmanager
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class LearnerSummary:
    id: str
    name: str
    text: str
    revision: int


class SummaryStore:
    def __init__(self, data_dir: Path):
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "study-summaries.sqlite3"
        with self.connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS learners (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    summary TEXT NOT NULL DEFAULT '',
                    revision INTEGER NOT NULL DEFAULT 0
                )
                """)

    @contextmanager
    def connect(self):
        with closing(sqlite3.connect(self.path, timeout=5)) as db, db:
            db.row_factory = sqlite3.Row
            yield db

    def create(self, name: str) -> str:
        name = name.strip()
        if not 1 <= len(name) <= 40:
            raise ValueError("Enter a learner name between 1 and 40 characters.")
        learner_id = uuid4().hex
        with self.connect() as db:
            db.execute("INSERT INTO learners (id, name) VALUES (?, ?)", (learner_id, name))
        return learner_id

    def profiles(self) -> dict[str, str]:
        with self.connect() as db:
            rows = db.execute("SELECT id, name FROM learners ORDER BY name, id").fetchall()
        return {row["id"]: row["name"] for row in rows}

    def get(self, learner_id: str) -> LearnerSummary:
        with self.connect() as db:
            row = db.execute(
                "SELECT id, name, summary, revision FROM learners WHERE id = ?", (learner_id,)
            ).fetchone()
        if row is None:
            raise KeyError("Learner profile is unavailable.")
        return LearnerSummary(row["id"], row["name"], row["summary"], row["revision"])

    def update(self, learner: LearnerSummary, text: str) -> bool:
        if len(text) > 3000:
            raise ValueError("The learner summary is too long.")
        with self.connect() as db:
            # A concurrent change wins over a summary based on an older revision.
            result = db.execute(
                """UPDATE learners SET summary = ?, revision = revision + 1
                   WHERE id = ? AND revision = ?""",
                (text, learner.id, learner.revision),
            )
            return result.rowcount == 1
