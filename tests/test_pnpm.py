"""Tests for pnpm builds and the pnpm audit report format.

Run: uv run --with pytest pytest tests
"""

import importlib
import json
import os
import types

import pytest

NPM_REPORT = {
    "vulnerabilities": {},
    "metadata": {
        "vulnerabilities": {"info": 0, "low": 1, "moderate": 2, "high": 0, "critical": 0, "total": 3},
        "dependencies": {"total": 50},
    },
}
# pnpm: no "total"; "dependencies" counts prod deps only, "totalDependencies" all of them
PNPM_REPORT = {
    "advisories": {},
    "metadata": {
        "vulnerabilities": {"info": 0, "low": 0, "moderate": 0, "high": 1, "critical": 1},
        "dependencies": 60,
        "totalDependencies": 77,
    },
}
CLEAN_PNPM_REPORT = {
    "advisories": {},
    "metadata": {
        "vulnerabilities": {"info": 0, "low": 0, "moderate": 0, "high": 0, "critical": 0},
        "dependencies": 5,
        "totalDependencies": 5,
    },
}


@pytest.fixture
def mods(tmp_path, monkeypatch):
    # viur_cli.conf writes config files into the cwd on import - keep them out of the repo.
    monkeypatch.chdir(tmp_path)
    return types.SimpleNamespace(
        build=importlib.import_module("viur_cli.build"),
        local=importlib.import_module("viur_cli.local"),
        utils=importlib.import_module("viur_cli.utils"),
    )


def _profile(builds):
    return {"sources_folder": "./sources", "distribution_folder": "./deploy", "builds": builds}


def _fake_audit(monkeypatch, local, builds, reports):
    """Use the given builds; pip-audit is clean, npm/pnpm return the given reports (exit 1 on findings)."""
    # config is None outside a viur project, so replace the whole object.
    monkeypatch.setattr(local, "config", types.SimpleNamespace(get_profile=lambda p: _profile(builds)))
    monkeypatch.setattr(local.shutil, "which", lambda tool: True)
    calls = []

    def run(cmd, **kwargs):
        calls.append((cmd, kwargs.get("cwd")))
        report = {"dependencies": []} if cmd[0] == "uvx" else reports[cmd[0]]
        found = any(v for k, v in report.get("metadata", {}).get("vulnerabilities", {}).items() if k != "total")
        return types.SimpleNamespace(returncode=int(found), stdout=json.dumps(report), stderr="")

    monkeypatch.setattr(local.subprocess, "run", run)
    return calls


def test_build_pnpm_runs_pnpm(mods, monkeypatch):
    cmds = []
    monkeypatch.setattr(mods.utils, "system", cmds.append)

    mods.build._build(_profile({}), "fe", {"kind": "pnpm", "source": "fe", "command": "build"}, ())
    mods.build._build(_profile({}), "fe", {"kind": "npm", "source": "fe", "command": "build"}, ())

    assert cmds == [
        "cd ./sources/fe && pnpm install && pnpm run build",
        "cd ./sources/fe && npm install && npm run build",
    ]


def test_clean_pnpm_drops_target_and_node_modules(mods, monkeypatch):
    removed = []
    monkeypatch.setattr(mods.utils, "rmdir", removed.append)

    mods.build._clean(_profile({}), "fe", {"kind": "pnpm", "source": "fe", "target": "fe"})

    assert removed == [os.path.join("./deploy", "fe"), os.path.join("./sources", "fe", "node_modules")]


def test_audit_reads_npm_and_pnpm_reports(mods, monkeypatch, capsys):
    calls = _fake_audit(monkeypatch, mods.local, {
        "a": {"kind": "npm", "source": "a"},
        "b": {"kind": "pnpm", "source": "b"},
        "c": {"kind": "exec", "command": "true"},
    }, {"npm": NPM_REPORT, "pnpm": PNPM_REPORT})

    assert mods.local.do_checks(dev=False) is False

    assert (["npm", "audit", "--json"], "./sources/a") in calls
    assert (["pnpm", "audit", "--json"], "./sources/b") in calls
    out = capsys.readouterr().out
    assert "Total Dependencies:     50" in out  # npm
    assert "Total Dependencies:     77" in out  # pnpm totalDependencies
    assert "Total Vulnerabilities:  3" in out
    assert "Total Vulnerabilities:  2" in out


def test_audit_clean_pnpm_passes(mods, monkeypatch):
    _fake_audit(monkeypatch, mods.local, {"b": {"kind": "pnpm", "source": "b"}}, {"pnpm": CLEAN_PNPM_REPORT})

    assert mods.local.do_checks(dev=False) is True
