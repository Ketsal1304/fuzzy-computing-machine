"""Command-line interface for the task manager."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Optional, Sequence

from .models import Task
from .repository import TaskRepository


def parse_date(value: str) -> date:
    """Parse a date string in ISO format."""

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        message = f"Invalid date '{value}'. Use the ISO format YYYY-MM-DD."
        raise argparse.ArgumentTypeError(message) from exc


def format_task(task: Task) -> str:
    """Return a human-readable representation of a task."""

    due = task.due_date.isoformat() if task.due_date else "—"
    status = "✓" if task.completed else "✗"
    description = f" — {task.description}" if task.description else ""
    return f"[{task.id}] {task.title} (due: {due}) [{status}]{description}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage a list of personal tasks")
    parser.add_argument(
        "--storage",
        default="tasks.json",
        help="Путь к файлу хранения задач (по умолчанию tasks.json).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="Показать список задач")
    list_parser.add_argument(
        "--completed",
        choices=["all", "yes", "no"],
        default="all",
        help="Фильтр по статусу выполнения",
    )
    list_parser.add_argument(
        "--due-before",
        type=parse_date,
        dest="due_before",
        help="Показать задачи с дедлайном не позже указанной даты",
    )

    add_parser = subparsers.add_parser("add", help="Создать новую задачу")
    add_parser.add_argument("title", help="Краткое описание задачи")
    add_parser.add_argument(
        "--description",
        default="",
        help="Дополнительное описание",
    )
    add_parser.add_argument(
        "--due",
        type=parse_date,
        dest="due_date",
        help="Дата завершения в формате YYYY-MM-DD",
    )

    update_parser = subparsers.add_parser("update", help="Обновить существующую задачу")
    update_parser.add_argument("task_id", type=int)
    update_parser.add_argument("--title")
    update_parser.add_argument("--description")
    update_parser.add_argument(
        "--clear-description",
        action="store_true",
        help="Очистить описание",
    )
    update_parser.add_argument(
        "--due",
        type=parse_date,
        dest="due_date",
        help="Новая дата завершения",
    )
    update_parser.add_argument(
        "--clear-due",
        action="store_true",
        help="Удалить дату завершения",
    )

    status_parser = subparsers.add_parser("complete", help="Отметить задачу выполненной")
    status_parser.add_argument("task_id", type=int)
    status_parser.add_argument(
        "--undo",
        action="store_true",
        help="Снять отметку о выполнении",
    )

    delete_parser = subparsers.add_parser("delete", help="Удалить задачу")
    delete_parser.add_argument("task_id", type=int)

    return parser


def list_tasks(repository: TaskRepository, args: argparse.Namespace) -> None:
    completed: Optional[bool]
    if args.completed == "yes":
        completed = True
    elif args.completed == "no":
        completed = False
    else:
        completed = None

    tasks = repository.list_tasks(completed=completed, due_before=args.due_before)
    if not tasks:
        print("Список задач пуст.")
        return

    for task in tasks:
        print(format_task(task))


def add_task(repository: TaskRepository, args: argparse.Namespace) -> None:
    task = repository.add_task(
        title=args.title,
        description=args.description,
        due_date=args.due_date,
    )
    print(f"Создана задача #{task.id}: {task.title}")


def update_task(repository: TaskRepository, args: argparse.Namespace) -> None:
    kwargs = {}
    if args.title is not None:
        kwargs["title"] = args.title
    if args.clear_description:
        kwargs["description"] = ""
    elif args.description is not None:
        kwargs["description"] = args.description
    if args.clear_due:
        kwargs["due_date"] = None
    elif args.due_date is not None:
        kwargs["due_date"] = args.due_date

    if not kwargs:
        print("Нет изменений для применения.")
        return

    task = repository.update_task(args.task_id, **kwargs)
    print(f"Задача #{task.id} обновлена.")


def set_status(repository: TaskRepository, args: argparse.Namespace) -> None:
    task = repository.update_task(args.task_id, completed=not args.undo)
    state = "выполнена" if task.completed else "возвращена в работу"
    print(f"Задача #{task.id} {state}.")


def delete_task(repository: TaskRepository, args: argparse.Namespace) -> None:
    repository.delete_task(args.task_id)
    print(f"Задача #{args.task_id} удалена.")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repository = TaskRepository(Path(args.storage))

    try:
        if args.command == "list":
            list_tasks(repository, args)
        elif args.command == "add":
            add_task(repository, args)
        elif args.command == "update":
            update_task(repository, args)
        elif args.command == "complete":
            set_status(repository, args)
        elif args.command == "delete":
            delete_task(repository, args)
        else:  # pragma: no cover - safeguard
            parser.error("Неизвестная команда")
    except KeyError as exc:
        task_id = exc.args[0]
        print(f"Ошибка: задача с идентификатором {task_id} не найдена.", file=sys.stderr)
        return 1
    except (ValueError, TypeError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

