"""Store individual learner facts and select notes by the question's topic."""

import re

from memorybench.memory.summaries import SummaryStore

NOTE_TOPICS = {
    "exam_date": r"\b(exam|test date|midterm|final exam)\b",
    "practice_topic": r"\b(struggl\w*|practice|exercise|topic|weakness)\b",
    "nickname": r"\b(nickname|call me)\b",
    "level": r"\b(level|beginner|intermediate|advanced|exercise)\b",
    "help_preference": r"\b(hint|hints|prefer\w*|exercise)\b",
    "study_group": r"\b(study group|group meeting|meeting time)\b",
}


class NoteStore(SummaryStore):
    """Reuse local learner profiles while keeping notes separate from summaries."""

    def __init__(self, data_dir):
        super().__init__(data_dir)
        with self.connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS study_notes (
                    learner_id TEXT NOT NULL REFERENCES learners(id),
                    topic TEXT NOT NULL,
                    fact TEXT NOT NULL,
                    PRIMARY KEY (learner_id, topic)
                )
                """)

    def notes(self, learner_id: str) -> dict[str, str]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT topic, fact FROM study_notes WHERE learner_id = ? ORDER BY topic",
                (learner_id,),
            ).fetchall()
        return {row["topic"]: row["fact"] for row in rows}

    def retrieve(self, learner_id: str, question: str) -> dict[str, str]:
        return {
            topic: fact
            for topic, fact in self.notes(learner_id).items()
            if re.search(NOTE_TOPICS[topic], question, re.IGNORECASE)
        }

    def save(self, learner_id: str, updates: dict[str, str]) -> None:
        if not isinstance(updates, dict) or any(
            topic not in NOTE_TOPICS
            or not isinstance(fact, str)
            or not 1 <= len(fact.strip()) <= 400
            for topic, fact in updates.items()
        ):
            raise ValueError("Invalid learner notes.")
        with self.connect() as db:
            db.execute("PRAGMA foreign_keys = ON")
            db.executemany(
                """INSERT INTO study_notes (learner_id, topic, fact) VALUES (?, ?, ?)
                   ON CONFLICT (learner_id, topic) DO UPDATE SET fact = excluded.fact""",
                [(learner_id, topic, fact.strip()) for topic, fact in updates.items()],
            )
