"""Dataclasses describing tasks and serialization helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, Optional


@dataclass
class Task:
    """Represents a single task in the application."""

    id: int
    title: str
    description: str = ""
    completed: bool = False
    due_date: Optional[date] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation of the task."""

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Task":
        """Instantiate a task from a dictionary payload."""

        due = payload.get("due_date")
        return cls(
            id=int(payload["id"]),
            title=str(payload["title"]),
            description=str(payload.get("description", "")),
            completed=bool(payload.get("completed", False)),
            due_date=date.fromisoformat(due) if due else None,
            created_at=datetime.fromisoformat(payload["created_at"]),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
        )


__all__ = ["Task"]

