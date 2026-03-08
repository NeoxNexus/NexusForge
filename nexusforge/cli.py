from __future__ import annotations

import argparse
import sys
from pathlib import Path

from nexusforge.backup import snapshot_vault
from nexusforge.capture import capture_idea_message
from nexusforge.config import load_config
from nexusforge.heartbeat import append_heartbeat_log, build_heartbeat_summary
from nexusforge.incubate import incubate_ideas
from nexusforge.storage import list_ideas
from nexusforge.webhook import start_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NexusForge local-first MVP CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Ensure vault directories exist")

    capture_parser = subparsers.add_parser("capture", help="Capture an idea from a prefixed message")
    capture_parser.add_argument("message", help="Message starting with 新点子： or idea:")
    capture_parser.add_argument("--source", default="manual", help="Capture source label")
    capture_parser.add_argument("--title", help="Override generated title")
    capture_parser.add_argument("--tags", help="Comma separated tags")

    list_parser = subparsers.add_parser("list", help="List ideas")
    list_parser.add_argument("--status", help="Filter by status")

    incubate_parser = subparsers.add_parser("incubate", help="Incubate pending ideas")
    incubate_parser.add_argument("--top", type=int, default=3, help="Number of ideas to incubate")
    incubate_parser.add_argument("--tag", help="Preferred tag when ranking pending ideas")
    incubate_parser.add_argument("--slug", help="Incubate a specific idea slug")
    incubate_parser.add_argument("--create-task", action="store_true", help="Create a task card or outbox payload")
    incubate_parser.add_argument("--mark-done", action="store_true", help="Mark idea as Done instead of Incubating")

    heartbeat_parser = subparsers.add_parser("heartbeat", help="Show pending idea summary")
    heartbeat_parser.add_argument("--limit", type=int, default=10, help="Limit number of ideas in summary")
    heartbeat_parser.add_argument("--log-only", action="store_true", help="Write log without printing")

    install_parser = subparsers.add_parser("install-heartbeat", help="Install daily cron heartbeat")
    install_parser.add_argument("--python", default=sys.executable, help="Python executable for cron")

    serve_parser = subparsers.add_parser("serve", help="Start a local webhook server")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)

    backup_parser = subparsers.add_parser("backup", help="Snapshot the vault with git")
    backup_parser.add_argument("--message", default="NexusForge vault snapshot")

    demo_parser = subparsers.add_parser("demo", help="Run an end-to-end local demo")
    demo_parser.add_argument(
        "--message",
        default="新点子：AI自动debug代码",
        help="Demo message to capture and incubate",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config()

    if args.command == "init":
        config.ensure_directories()
        print(f"环境就绪。Vault root: {config.vault_root}")
        return 0

    if args.command == "capture":
        custom_tags = [item.strip() for item in args.tags.split(",")] if args.tags else None
        idea, path = capture_idea_message(
            args.message,
            config,
            source=args.source,
            title=args.title,
            tags=custom_tags,
        )
        print(f"Idea captured! Stored as {idea.title}.")
        print(path)
        return 0

    if args.command == "list":
        config.ensure_directories()
        ideas = list_ideas(config.ideas_dir)
        if args.status:
            ideas = [idea for idea in ideas if idea.status == args.status]
        for idea in ideas:
            print(f"{idea.slug}\t{idea.status}\t{idea.title}\t{', '.join(idea.tags)}")
        return 0

    if args.command == "incubate":
        results = incubate_ideas(
            config,
            top=args.top,
            preferred_tag=args.tag,
            slug=args.slug,
            create_task=args.create_task,
            mark_done=args.mark_done,
        )
        if not results:
            print("No matching New ideas to incubate.")
            return 0
        for result in results:
            print(f"{result.idea.slug}\t{result.idea.status}\t{result.report_path}")
            if result.task_card_id:
                print(f"task_card={result.task_card_id}\tlocation={result.task_card_location}")
        return 0

    if args.command == "heartbeat":
        summary = build_heartbeat_summary(config, limit=args.limit)
        log_path = append_heartbeat_log(config, summary)
        if not args.log_only:
            print(summary)
            print(f"Logged to {log_path}")
        return 0

    if args.command == "install-heartbeat":
        install_heartbeat_cron(config, python_executable=args.python)
        print("Heartbeat cron installed.")
        return 0

    if args.command == "serve":
        config.ensure_directories()
        print(f"Serving NexusForge webhook on http://{args.host}:{args.port}")
        start_server(config, host=args.host, port=args.port)
        return 0

    if args.command == "backup":
        result = snapshot_vault(config.vault_root, message=args.message)
        print(result)
        return 0

    if args.command == "demo":
        run_demo(config, args.message)
        return 0

    parser.print_help()
    return 1


def install_heartbeat_cron(config, python_executable: str) -> None:
    import subprocess

    config.ensure_directories()
    command = (
        f"{config.cron_minute} {config.cron_hour} * * * "
        f"cd {config.project_root} && {python_executable} -m nexusforge.cli heartbeat --limit 10 --log-only "
        f">> {config.logs_dir / 'heartbeat.log'} 2>&1"
    )
    block = "\n".join(
        [
            "# NexusForge heartbeat start",
            f"CRON_TZ={config.cron_timezone}",
            command,
            "# NexusForge heartbeat end",
        ]
    )

    current = subprocess.run(
        ["crontab", "-l"],
        text=True,
        capture_output=True,
        check=False,
    ).stdout

    if "# NexusForge heartbeat start" in current:
        before = current.split("# NexusForge heartbeat start", 1)[0].rstrip()
        after = current.split("# NexusForge heartbeat end", 1)[-1].lstrip()
        current = "\n".join(part for part in (before, after) if part).strip()

    new_content = "\n".join(part for part in (current.strip(), block) if part).strip() + "\n"
    subprocess.run(["crontab", "-"], input=new_content, text=True, check=True)


def run_demo(config, message: str) -> None:
    config.ensure_directories()
    idea, idea_path = capture_idea_message(message, config, source="demo")
    print(f"captured={idea_path}")
    results = incubate_ideas(config, slug=idea.slug, create_task=True)
    for result in results:
        print(f"report={result.report_path}")
        if result.task_card_id:
            print(f"task_card={result.task_card_id}")
    summary = build_heartbeat_summary(config, limit=10)
    append_heartbeat_log(config, summary)
    print(summary)
    print(snapshot_vault(config.vault_root, message="NexusForge demo snapshot"))


if __name__ == "__main__":
    raise SystemExit(main())

