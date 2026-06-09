"""Tests für den reinen Build-Step-Kern.

Dieses Modul importiert ausschließlich ``viur_cli.build_steps`` — und damit nur
``viur_cli.utils`` (seiteneffektfrei). Es triggert **nicht** ``viur_cli.conf``,
das beim Import die ``project.json``-Suche samt ``os.chdir`` ausführen würde.
Entsprechend braucht keiner dieser Tests ein echtes Projekt, ein subprocess oder
ein bestimmtes Arbeitsverzeichnis.
"""

from pathlib import Path

import pytest

from viur_cli.build_steps import BuildStep, ExecBuildStep, NpmBuildStep, from_config

CONF = {"sources_folder": "sources", "distribution_folder": "deploy"}


# --- from_config -------------------------------------------------------------

def test_from_config_npm_minimal() -> None:
    step = from_config("ui", {"kind": "npm", "command": "build", "source": "frontend"})
    assert isinstance(step, NpmBuildStep)
    assert step.name == "ui"
    assert step.command == "build"
    assert step.source == "frontend"
    assert step.target is None
    assert step.args == ()
    assert step.env == {}


def test_from_config_npm_full() -> None:
    step = from_config("ui", {
        "kind": "npm", "command": "build", "source": "frontend",
        "target": "ui", "version": "1.2.3", "clean": "rm -rf x",
        "args": ["--mode", "prod"], "env": {"A": "1"},
    })
    assert isinstance(step, NpmBuildStep)
    assert step.target == "ui"
    assert step.version == "1.2.3"
    assert step.clean_cmd == "rm -rf x"
    assert step.args == ("--mode", "prod")
    assert step.env == {"A": "1"}


def test_from_config_exec() -> None:
    step = from_config("admin", {
        "kind": "exec", "command": "viur package install admin", "version": "4.0.8",
    })
    assert isinstance(step, ExecBuildStep)
    assert step.command == "viur package install admin"
    assert step.version == "4.0.8"


def test_from_config_unknown_kind_raises() -> None:
    with pytest.raises(ValueError):
        from_config("x", {"kind": "wat", "command": "y"})


# --- build_command: npm ------------------------------------------------------

def test_npm_build_command_no_args() -> None:
    step = from_config("ui", {"kind": "npm", "command": "build", "source": "frontend"})
    assert step.build_command(CONF, ()) == "npm install && npm run build"


def test_npm_build_command_with_extra_args() -> None:
    step = from_config("ui", {"kind": "npm", "command": "build", "source": "frontend"})
    cmd = step.build_command(CONF, ("--mode", "production"))
    assert cmd == "npm install && npm run build -- --mode production"


def test_npm_build_command_merges_config_then_cli_args() -> None:
    step = from_config("ui", {
        "kind": "npm", "command": "build", "source": "f", "args": ["--base", "/x/"],
    })
    cmd = step.build_command(CONF, ("--mode", "prod"))
    assert cmd == "npm install && npm run build -- --base /x/ --mode prod"


def test_npm_build_command_quotes_args_with_spaces() -> None:
    step = from_config("ui", {"kind": "npm", "command": "build", "source": "f"})
    cmd = step.build_command(CONF, ("--title", "hello world"))
    assert cmd == "npm install && npm run build -- --title 'hello world'"


# --- build_command: exec -----------------------------------------------------

def test_exec_build_command_no_args() -> None:
    step = from_config("admin", {"kind": "exec", "command": "viur package install admin"})
    assert step.build_command(CONF, ()) == "viur package install admin"


def test_exec_build_command_with_args() -> None:
    step = from_config("admin", {"kind": "exec", "command": "mytool", "args": ["--x"]})
    assert step.build_command(CONF, ("--y", "z")) == "mytool --x --y z"


# --- resolve_cwd -------------------------------------------------------------

def test_npm_resolve_cwd() -> None:
    step = from_config("ui", {"kind": "npm", "command": "build", "source": "frontend"})
    assert step.resolve_cwd(CONF) == Path("sources/frontend")


def test_npm_resolve_cwd_empty_source() -> None:
    step = from_config("ui", {"kind": "npm", "command": "build", "source": ""})
    assert step.resolve_cwd(CONF) == Path("sources")


def test_exec_resolve_cwd_is_none() -> None:
    step = from_config("admin", {"kind": "exec", "command": "x"})
    assert step.resolve_cwd(CONF) is None


# --- resolve_env -------------------------------------------------------------

def test_resolve_env_returns_only_overrides() -> None:
    step = from_config("ui", {
        "kind": "npm", "command": "build", "source": "f", "env": {"A": "1", "B": "2"},
    })
    env = step.resolve_env(CONF, {})
    assert env == {"A": "1", "B": "2"}
    assert "PATH" not in env  # os.environ wird NICHT eingemischt


def test_resolve_env_cli_overrides_config() -> None:
    step = from_config("ui", {
        "kind": "npm", "command": "build", "source": "f", "env": {"A": "1", "B": "2"},
    })
    env = step.resolve_env(CONF, {"B": "99", "C": "3"})
    assert env == {"A": "1", "B": "99", "C": "3"}


def test_resolve_env_expands_placeholders() -> None:
    conf = {**CONF, "application_name": "myapp"}
    step = from_config("ui", {
        "kind": "npm", "command": "build", "source": "f",
        "env": {"TARGET": "x-$(application_name)"},
    })
    assert step.resolve_env(conf, {}) == {"TARGET": "x-myapp"}


def test_resolve_env_empty_is_empty() -> None:
    step = from_config("admin", {"kind": "exec", "command": "x"})
    assert step.resolve_env(CONF, {}) == {}


def test_resolve_env_does_not_mutate_step() -> None:
    step = from_config("ui", {
        "kind": "npm", "command": "build", "source": "f", "env": {"A": "1"},
    })
    step.resolve_env(CONF, {"B": "2"})
    assert step.env == {"A": "1"}


# --- Dataclass-Eigenschaften -------------------------------------------------

def test_env_default_not_shared() -> None:
    s1 = ExecBuildStep(name="a", command="x")
    s2 = ExecBuildStep(name="b", command="y")
    s1.env["K"] = "v"  # frozen verhindert nur Attribut-Reassign, nicht dict-Mutation
    assert s2.env == {}


def test_step_is_frozen() -> None:
    step = from_config("admin", {"kind": "exec", "command": "x"})
    with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
        step.command = "y"  # type: ignore[misc]


def test_base_build_command_not_implemented() -> None:
    step = BuildStep(name="x", command="y")
    with pytest.raises(NotImplementedError):
        step.build_command(CONF, ())
