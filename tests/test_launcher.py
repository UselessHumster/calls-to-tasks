import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from calls import launcher, pipeline


def test_default_and_local_precedence(tmp_path, monkeypatch):
    settings = tmp_path / "settings.local.toml"
    monkeypatch.setattr(launcher, "SETTINGS", settings)
    monkeypatch.delenv("CALLS_CODEX_COMMAND", raising=False)
    assert launcher.default_command() == "codex"
    settings.write_text('[codex]\ncommand = "codex-s"\n')
    assert launcher.default_command() == "codex-s"
    monkeypatch.setenv("CALLS_CODEX_COMMAND", "codex-other")
    assert launcher.default_command() == "codex-other"


def test_executable_does_not_use_shell():
    with patch.object(launcher.shutil, "which", return_value="/bin/codex"):
        assert launcher.launch_command("codex", ["exec", "-"]) == ["/bin/codex", "exec", "-"]


def test_alias_loads_from_zshrc_and_arguments_stay_literal(tmp_path, monkeypatch):
    shell = shutil.which("zsh")
    if not shell:
        pytest.skip("zsh is not installed")
    monkeypatch.setenv("SHELL", shell)
    monkeypatch.setenv("ZDOTDIR", str(tmp_path))
    (tmp_path / ".zshrc").write_text("alias calls_test_alias='printf \"%s\\n\"'\n")
    argument = 'space; $(echo should-not-run) "quoted"'
    result = subprocess.run(
        launcher.launch_command("calls_test_alias", [argument]),
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == argument


def test_rejects_shell_expression():
    with pytest.raises(ValueError):
        launcher.launch_command("codex; echo bad", [])


@pytest.mark.parametrize("override", [None, "~/work-codex"])
def test_auth_environment_is_inherited_unless_overridden(tmp_path, monkeypatch, override):
    monkeypatch.setenv("CODEX_HOME", "/existing/codex")
    monkeypatch.delenv("CALLS_CODEX_HOME", raising=False)
    if override:
        monkeypatch.setenv("CALLS_CODEX_HOME", override)

    def run(command, **kwargs):
        expected = str(Path(override).expanduser()) if override else "/existing/codex"
        assert kwargs["env"]["CODEX_HOME"] == expected
        Path(command[command.index("-o") + 1]).write_text("done")
        return subprocess.CompletedProcess(command, 0)

    with (
        patch.object(pipeline, "launch_command", side_effect=lambda name, args: [name, *args]),
        patch.object(pipeline.subprocess, "run", side_effect=run),
    ):
        assert pipeline.codex("test", "model", tmp_path, "codex") == "done"


def test_no_implicit_codex_s_home(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_HOME", raising=False)
    monkeypatch.delenv("CALLS_CODEX_HOME", raising=False)

    def run(command, **kwargs):
        assert "CODEX_HOME" not in kwargs["env"]
        Path(command[command.index("-o") + 1]).write_text("done")
        return subprocess.CompletedProcess(command, 0)

    with (
        patch.object(pipeline, "launch_command", side_effect=lambda name, args: [name, *args]),
        patch.object(pipeline.subprocess, "run", side_effect=run),
    ):
        pipeline.codex("test", "model", tmp_path, "codex")
