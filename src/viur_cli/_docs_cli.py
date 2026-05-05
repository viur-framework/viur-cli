"""Docs-only entry point for mkdocs-click.

mkdocs-click introspects the Click group object at import time. The runtime
entry point `viur_cli.cli:main` attaches all subcommands by importing each
submodule explicitly (their `@cli.command`/`@cli.group` decorators bind to
the root group at import time). Without invoking main(), only the commands
defined directly in `cli.py` are visible.

This module performs the same side-effect imports so that `from
viur_cli._docs_cli import cli` returns a fully populated Click group —
suitable for static introspection by mkdocs-click.
"""
from viur_cli import build  # noqa: F401
from viur_cli import cloud  # noqa: F401
from viur_cli import deprecated  # noqa: F401
from viur_cli import local  # noqa: F401
from viur_cli import package  # noqa: F401
from viur_cli import setup  # noqa: F401
from viur_cli import update  # noqa: F401
from viur_cli.scriptor import script  # noqa: F401

from viur_cli.cli import cli

__all__ = ["cli"]
