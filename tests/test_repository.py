"""Unit tests for the task repository."""

from __future__ import annotations

import unittest
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from task_app.repository import TaskRepository


class TaskRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.storage_path = Path(self._tmpdir.name) / "tasks.json"
        self.repository = TaskRepository(self.storage_path)

    def test_add_and_list_tasks(self) -> None:
        first = self.repository.add_task("Write documentation")
        second = self.repository.add_task("Implement feature", description="Add API endpoint")

        tasks = self.repository.list_tasks()
        self.assertEqual([task.id for task in tasks], [first.id, second.id])
        self.assertEqual(tasks[1].description, "Add API endpoint")

    def test_persistence_across_instances(self) -> None:
        created = self.repository.add_task("Plan release")
        another = TaskRepository(self.storage_path)
        loaded = another.list_tasks()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].title, "Plan release")
        self.assertEqual(loaded[0].id, created.id)

    def test_update_task_fields(self) -> None:
        due = date.today()
        task = self.repository.add_task("Prepare report", description="Collect metrics", due_date=due)

        new_due = due + timedelta(days=2)
        updated = self.repository.update_task(
            task.id,
            title="Prepare annual report",
            description="Compile yearly metrics",
            due_date=new_due,
        )

        self.assertEqual(updated.title, "Prepare annual report")
        self.assertEqual(updated.description, "Compile yearly metrics")
        self.assertEqual(updated.due_date, new_due)
        self.assertGreaterEqual(updated.updated_at, updated.created_at)

    def test_update_can_clear_fields(self) -> None:
        task = self.repository.add_task("Schedule meeting", description="Discuss roadmap", due_date=date.today())

        updated = self.repository.update_task(task.id, description="", due_date=None)
        self.assertEqual(updated.description, "")
        self.assertIsNone(updated.due_date)

    def test_update_accepts_status_changes(self) -> None:
        task = self.repository.add_task("Write unit tests")
        marked = self.repository.update_task(task.id, completed=True)
        self.assertTrue(marked.completed)
        reopened = self.repository.update_task(task.id, completed=False)
        self.assertFalse(reopened.completed)

    def test_delete_task(self) -> None:
        task = self.repository.add_task("Trim backlog")
        self.repository.delete_task(task.id)
        self.assertEqual(self.repository.list_tasks(), [])
        with self.assertRaises(KeyError):
            self.repository.get_task(task.id)

    def test_list_filters(self) -> None:
        today = date.today()
        tomorrow = today + timedelta(days=1)

        early = self.repository.add_task("Pay invoices", due_date=today)
        late = self.repository.add_task("Plan sprint", due_date=tomorrow)
        self.repository.update_task(late.id, completed=True)

        completed = self.repository.list_tasks(completed=True)
        self.assertEqual([task.id for task in completed], [late.id])

        due_before = self.repository.list_tasks(due_before=today)
        self.assertEqual([task.id for task in due_before], [early.id])

    def test_validation_errors(self) -> None:
        with self.assertRaises(ValueError):
            self.repository.add_task("   ")

        task = self.repository.add_task("Initial title")
        with self.assertRaises(ValueError):
            self.repository.update_task(task.id, title="   ")
        with self.assertRaises(TypeError):
            self.repository.update_task(task.id, due_date="2024-01-01")  # type: ignore[arg-type]


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

