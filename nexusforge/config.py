from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PREFIXES = ("新点子：", "新点子:", "idea:", "idea：")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "nexusforge.toml"


@dataclass
class Config:
    vault_root: Path
    ideas_dir: Path
    incubations_dir: Path
    taskboard_outbox_dir: Path
    logs_dir: Path
    vault_timezone: str = "America/Los_Angeles"
    taskboard_endpoint: str = ""
    taskboard_api_key: str = ""
    cron_timezone: str = "America/Los_Angeles"
    cron_hour: int = 9
    cron_minute: int = 0
    capture_prefixes: tuple[str, ...] = DEFAULT_PREFIXES
    project_root: Path = PROJECT_ROOT

    def ensure_directories(self) -> None:
        for path in (
            self.vault_root,
            self.ideas_dir,
            self.incubations_dir,
            self.taskboard_outbox_dir,
            self.logs_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


def load_config(config_path: Path | None = None) -> Config:
    path = config_path or Path(os.environ.get("NEXUSFORGE_CONFIG", DEFAULT_CONFIG_PATH))
    data: dict[str, object] = {}
    if path.exists():
        with path.open("rb") as handle:
            data = tomllib.load(handle)

    vault_cfg = _section(data, "vault")
    task_cfg = _section(data, "taskboard")
    heartbeat_cfg = _section(data, "heartbeat")

    vault_root = Path(
        os.environ.get(
            "NEXUSFORGE_VAULT_ROOT",
            str(vault_cfg.get("root", Path.home() / "ideas-vault")),
        )
    ).expanduser()
    ideas_dir = vault_root / str(vault_cfg.get("ideas_dir", "ideas"))
    incubations_dir = vault_root / str(vault_cfg.get("incubations_dir", "incubations"))
    taskboard_outbox_dir = vault_root / str(
        vault_cfg.get("taskboard_outbox_dir", "taskboard-outbox")
    )
    logs_dir = vault_root / str(vault_cfg.get("logs_dir", "logs"))

    return Config(
        vault_root=vault_root,
        ideas_dir=ideas_dir,
        incubations_dir=incubations_dir,
        taskboard_outbox_dir=taskboard_outbox_dir,
        logs_dir=logs_dir,
        vault_timezone=os.environ.get(
            "NEXUSFORGE_VAULT_TIMEZONE",
            str(vault_cfg.get("timezone", "America/Los_Angeles")),
        ),
        taskboard_endpoint=os.environ.get(
            "NEXUSFORGE_TASKBOARD_ENDPOINT", str(task_cfg.get("endpoint", ""))
        ),
        taskboard_api_key=os.environ.get(
            "NEXUSFORGE_TASKBOARD_API_KEY", str(task_cfg.get("api_key", ""))
        ),
        cron_timezone=os.environ.get(
            "NEXUSFORGE_CRON_TIMEZONE", str(heartbeat_cfg.get("cron_timezone", "America/Los_Angeles"))
        ),
        cron_hour=int(os.environ.get("NEXUSFORGE_CRON_HOUR", heartbeat_cfg.get("hour", 9))),
        cron_minute=int(
            os.environ.get("NEXUSFORGE_CRON_MINUTE", heartbeat_cfg.get("minute", 0))
        ),
    )


def _section(data: dict[str, object], key: str) -> dict[str, object]:
    value = data.get(key, {})
    if isinstance(value, dict):
        return value
    return {}
