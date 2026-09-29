"""Resolve the standard CLI or a user's shell alias."""

import os
import re
import shutil
import tomllib
from pathlib import Path

SETTINGS = Path(__file__).resolve().parent.parent / "settings.local.toml"


def default_command() -> str:
    if value := os.environ.get("CALLS_CODEX_COMMAND"):
        return value
    if SETTINGS.exists():
        with SETTINGS.open("rb") as f:
            return tomllib.load(f).get("codex", {}).get("command", "codex")
    return "codex"


def launch_command(command: str, arguments: list[str]) -> list[str]:
    command = command.strip()
    if binary := shutil.which(command):
        return [binary, *arguments]
    # Only a command name is inserted into shell code; arguments stay positional.
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_-]*", command):
        raise ValueError("Укажи имя команды/алиаса или путь к исполняемому файлу, без аргументов.")
    shell = os.environ.get("SHELL", "/bin/zsh")
    if Path(shell).name not in {"zsh", "bash"}:
        raise ValueError(
            "Для shell-алиасов нужен zsh или bash. Можно указать путь к wrapper-скрипту."
        )
    return [shell, "-ic", f'{command} "$@"', "calls-to-tasks", *arguments]
