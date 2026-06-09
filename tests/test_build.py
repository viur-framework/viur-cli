"""Tests für die Build-CLI (Argument-/Options-Parsing, Pass-through, Env).

Statt echte Subprozesse zu starten, ersetzt die ``recorded_system``-Fixture
``utils.system`` durch einen Recorder und prüft das gebaute Kommando bzw. die
Env. Die Projekt-Config wird durch eine ``_FakeConfig`` ersetzt (kein
``project.json`` nötig).
"""

import pytest
from click.testing import CliRunner

from viur_cli import build as build_mod
from viur_cli.build import _parse_env, build


class _FakeConfig:
    def __init__(self, builds: dict) -> None:
        self._builds = builds

    def get_profile(self, profile: str) -> dict:
        return {"sources_folder": "sources", "distribution_folder": "deploy", "builds": self._builds}


@pytest.fixture
def recorded_system(monkeypatch):
    calls: list[dict] = []

    def fake_system(cmd, *, cwd=None, env=None):
        calls.append({"cmd": cmd, "cwd": cwd, "env": env})

    monkeypatch.setattr("viur_cli.utils.system", fake_system)
    return calls


def _use_config(monkeypatch, builds: dict) -> None:
    monkeypatch.setattr(build_mod, "config", _FakeConfig(builds))


# --- _parse_env --------------------------------------------------------------

def test_parse_env_ok() -> None:
    assert _parse_env(("A=1", "B=2")) == {"A": "1", "B": "2"}


def test_parse_env_value_with_equals() -> None:
    assert _parse_env(("DOMAINS=@a.de,@b.de", "URL=https://x/y=z"),) == {
        "DOMAINS": "@a.de,@b.de", "URL": "https://x/y=z",
    }


def test_parse_env_empty_value_allowed() -> None:
    assert _parse_env(("A=",)) == {"A": ""}


def test_parse_env_missing_equals_aborts() -> None:
    with pytest.raises(SystemExit):
        _parse_env(("BAD",))


def test_parse_env_empty_key_aborts() -> None:
    with pytest.raises(SystemExit):
        _parse_env(("=x",))


# --- app: Pass-through + Optionen --------------------------------------------

def test_app_passes_through_extra_args(monkeypatch, recorded_system) -> None:
    _use_config(monkeypatch, {"ui": {"kind": "npm", "command": "build", "source": ""}})
    result = CliRunner().invoke(build, ["app", "ui", "-p", "default", "--", "--mode", "staging"])
    assert result.exit_code == 0, result.output
    assert recorded_system[-1]["cmd"] == "npm install && npm run build -- --mode staging"


def test_app_passes_through_without_double_dash(monkeypatch, recorded_system) -> None:
    _use_config(monkeypatch, {"ui": {"kind": "npm", "command": "build", "source": ""}})
    result = CliRunner().invoke(build, ["app", "ui", "--mode", "staging"])
    assert result.exit_code == 0, result.output
    assert recorded_system[-1]["cmd"] == "npm install && npm run build -- --mode staging"


def test_app_sets_env(monkeypatch, recorded_system) -> None:
    _use_config(monkeypatch, {"x": {"kind": "exec", "command": "echo hi"}})
    result = CliRunner().invoke(build, ["app", "x", "-e", "FOO=bar", "-e", "BAZ=1"])
    assert result.exit_code == 0, result.output
    assert recorded_system[-1]["env"]["FOO"] == "bar"
    assert recorded_system[-1]["env"]["BAZ"] == "1"


def test_app_unknown_name_fails(monkeypatch, recorded_system) -> None:
    _use_config(monkeypatch, {"ui": {"kind": "exec", "command": "x"}})
    result = CliRunner().invoke(build, ["app", "nope"])
    assert result.exit_code != 0


# --- release: nur -v/-e, kein Pass-through -----------------------------------

def test_release_runs_all_steps_in_order(monkeypatch, recorded_system) -> None:
    _use_config(monkeypatch, {
        "a": {"kind": "exec", "command": "echo a"},
        "b": {"kind": "exec", "command": "echo b"},
    })
    result = CliRunner().invoke(build, ["release"])
    assert result.exit_code == 0, result.output
    assert [c["cmd"] for c in recorded_system] == ["echo a", "echo b"]


def test_release_env_applies_to_all_steps(monkeypatch, recorded_system) -> None:
    _use_config(monkeypatch, {
        "a": {"kind": "exec", "command": "echo a"},
        "b": {"kind": "exec", "command": "echo b"},
    })
    result = CliRunner().invoke(build, ["release", "-e", "K=v"])
    assert result.exit_code == 0, result.output
    assert all(c["env"]["K"] == "v" for c in recorded_system)


def test_release_rejects_unknown_option(monkeypatch, recorded_system) -> None:
    _use_config(monkeypatch, {"a": {"kind": "exec", "command": "echo a"}})
    result = CliRunner().invoke(build, ["release", "--bogus"])
    assert result.exit_code != 0
    assert not recorded_system  # nichts gelaufen


def test_unknown_kind_aborts(monkeypatch, recorded_system) -> None:
    _use_config(monkeypatch, {"a": {"kind": "weird", "command": "x"}})
    result = CliRunner().invoke(build, ["release"])
    assert result.exit_code != 0
