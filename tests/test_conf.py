"""Tests für den tiefen ``builds``-Merge in ``ProjectConfig.get_profile``."""

from viur_cli.conf import ProjectConfig, _merge_builds


def _make_config(data: dict) -> ProjectConfig:
    """ProjectConfig-Instanz ohne ``load()`` (kein project.json, kein chdir)."""
    cfg = ProjectConfig.__new__(ProjectConfig)
    cfg.update(data)
    return cfg


# --- _merge_builds (reine Funktion) ------------------------------------------

def test_merge_builds_profile_overrides_field() -> None:
    base = {"ui": {"kind": "npm", "command": "build", "source": "f"}}
    override = {"ui": {"command": "build:prod"}}
    merged = _merge_builds(base, override)
    assert merged["ui"]["command"] == "build:prod"
    assert merged["ui"]["source"] == "f"


def test_merge_builds_merges_env() -> None:
    base = {"ui": {"kind": "npm", "command": "build", "env": {"A": "1", "B": "2"}}}
    override = {"ui": {"env": {"B": "99", "C": "3"}}}
    merged = _merge_builds(base, override)
    assert merged["ui"]["env"] == {"A": "1", "B": "99", "C": "3"}


def test_merge_builds_keeps_base_only_builds() -> None:
    base = {"admin": {"kind": "exec", "command": "x"}, "ui": {"kind": "npm", "command": "build"}}
    override = {"ui": {"command": "build:prod"}}
    merged = _merge_builds(base, override)
    assert "admin" in merged


def test_merge_builds_adds_profile_only_builds() -> None:
    base = {"ui": {"kind": "npm", "command": "build"}}
    override = {"extra": {"kind": "exec", "command": "y"}}
    merged = _merge_builds(base, override)
    assert merged["extra"] == {"kind": "exec", "command": "y"}
    assert "ui" in merged


def test_merge_builds_does_not_mutate_inputs() -> None:
    base = {"ui": {"kind": "npm", "command": "build", "env": {"A": "1"}}}
    override = {"ui": {"env": {"B": "2"}}}
    _merge_builds(base, override)
    assert base["ui"]["env"] == {"A": "1"}
    assert override["ui"]["env"] == {"B": "2"}


# --- get_profile (Integration) -----------------------------------------------

def test_get_profile_deep_merges_builds() -> None:
    cfg = _make_config({
        "format": "2.0.0",
        "default": {
            "application_name": "live",
            "builds": {
                "admin": {"kind": "exec", "command": "viur package install admin"},
                "ui": {"kind": "npm", "command": "build", "source": "f", "env": {"T": "live"}},
            },
        },
        "develop": {
            "application_name": "dev",
            "builds": {"ui": {"env": {"T": "dev", "X": "1"}}},
        },
    })
    profile = cfg.get_profile("develop")
    assert profile["application_name"] == "dev"               # flacher Override
    assert "admin" in profile["builds"]                       # default-Build bleibt
    assert profile["builds"]["ui"]["source"] == "f"           # default-Feld bleibt
    assert profile["builds"]["ui"]["env"] == {"T": "dev", "X": "1"}  # env gemergt


def test_get_profile_without_profile_builds_uses_default() -> None:
    cfg = _make_config({
        "format": "2.0.0",
        "default": {"builds": {"ui": {"kind": "npm", "command": "build"}}},
        "develop": {"application_name": "dev"},
    })
    profile = cfg.get_profile("develop")
    assert profile["builds"] == {"ui": {"kind": "npm", "command": "build"}}


def test_get_profile_does_not_mutate_default() -> None:
    cfg = _make_config({
        "format": "2.0.0",
        "default": {"builds": {"ui": {"kind": "npm", "command": "build", "env": {"A": "1"}}}},
        "develop": {"builds": {"ui": {"env": {"B": "2"}}}},
    })
    cfg.get_profile("develop")
    assert cfg["default"]["builds"]["ui"]["env"] == {"A": "1"}
