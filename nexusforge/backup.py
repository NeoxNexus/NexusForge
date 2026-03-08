from __future__ import annotations

import subprocess
from pathlib import Path


def snapshot_vault(vault_root: Path, message: str = "NexusForge vault snapshot") -> str:
    vault_root.mkdir(parents=True, exist_ok=True)
    _run(["git", "init"], cwd=vault_root)
    _run(["git", "add", "."], cwd=vault_root)
    diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=vault_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if diff.returncode == 0:
        return "Vault snapshot skipped: no staged changes."

    _run(
        [
            "git",
            "-c",
            "user.name=NexusForge",
            "-c",
            "user.email=nexusforge@local",
            "commit",
            "-m",
            message,
        ],
        cwd=vault_root,
    )
    return f"Vault snapshot created in {vault_root}"


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )

