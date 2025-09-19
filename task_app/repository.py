"""Repository that stores tasks in memory and optional JSON storage."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .models import Task

_SENTINEL = object()


class TaskRepository:
    """Manage tasks in memory with optional persistence to a JSON file."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self._storage_path = Path(storage_path) if storage_path else None
        self._tasks: Dict[int, Task] = {}
        self._next_id = 1
        if self._storage_path:
            self._load()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if self._storage_path is None or not self._storage_path.exists():
            return

        with self._storage_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        for item in payload:
            task = Task.from_dict(item)
            self._tasks[task.id] = task

        if self._tasks:
            self._next_id = max(self._tasks) + 1
        else:
            self._next_id = 1

    def _save(self) -> None:
        if self._storage_path is None:
            return

        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        serialised = [task.to_dict() for task in self.list_tasks()]
        with self._storage_path.open("w", encoding="utf-8") as handle:
            json.dump(serialised, handle, indent=2)

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def list_tasks(
        self,
        *,
        completed: Optional[bool] = None,
        due_before: Optional[date] = None,
    ) -> List[Task]:
        tasks: Iterable[Task] = self._tasks.values()

        if completed is not None:
            tasks = (task for task in tasks if task.completed == completed)

        if due_before is not None:
            tasks = (
                task
                for task in tasks
                if task.due_date is not None and task.due_date <= due_before
            )

        return sorted(tasks, key=lambda item: item.id)

    def add_task(
        self,
        title: str,
        description: str = "",
        due_date: Optional[date] = None,
    ) -> Task:
        title = title.strip()
        if not title:
            raise ValueError("Task title must not be empty.")

        now = datetime.utcnow()
        task = Task(
            id=self._next_id,
            title=title,
            description=(description or "").strip(),
            completed=False,
            due_date=due_date,
            created_at=now,
            updated_at=now,
        )
        self._tasks[task.id] = task
        self._next_id += 1
        self._save()
        return task

    def get_task(self, task_id: int) -> Task:
        try:
            return self._tasks[task_id]
        except KeyError as error:
            raise KeyError(task_id) from error

    def update_task(
        self,
        task_id: int,
        *,
        title: Optional[str] = None,
        description: object = _SENTINEL,
        due_date: object = _SENTINEL,
        completed: Optional[bool] = None,
    ) -> Task:
        task = self.get_task(task_id)
        changed = False

        if title is not None:
            new_title = title.strip()
            if not new_title:
                raise ValueError("Task title must not be empty.")
            task.title = new_title
            changed = True

        if description is not _SENTINEL:
            task.description = (description or "").strip()
            changed = True

        if due_date is not _SENTINEL:
            if due_date is None:
                task.due_date = None
            elif isinstance(due_date, date):
                task.due_date = due_date
            else:
                raise TypeError("due_date must be a date object or None.")
            changed = True

        if completed is not None:
            task.completed = completed
            changed = True

        if changed:
            task.updated_at = datetime.utcnow()
            self._tasks[task_id] = task
            self._save()

        return task

    def delete_task(self, task_id: int) -> None:
        try:
            del self._tasks[task_id]
        except KeyError as error:
            raise KeyError(task_id) from error
        else:
            self._save()

    # ------------------------------------------------------------------
    # Testing helpers
    # ------------------------------------------------------------------
    def clear(self) -> None:
        self._tasks.clear()
        self._next_id = 1
        if self._storage_path:
            self._storage_path.unlink(missing_ok=True)


__all__ = ["TaskRepository"]

