"""Build pipeline for ViUR projects: orchestrates npm and exec build steps.

The actual per-step behaviour lives in :mod:`viur_cli.build_steps`; this module
is the thin Click layer that resolves a profile, turns its ``builds`` section
into :class:`~viur_cli.build_steps.BuildStep` objects and runs/cleans them.

Flags and env can be supplied two ways and combine: statically per build via the
``args`` / ``env`` fields in ``project.json``, and at runtime via the CLI. Arbitrary
pass-through args are only accepted by ``app`` (a single, named build); ``release``
takes just ``-v`` and ``-e`` (applied to every step).
"""

import typing as t

import click

from . import utils
from .build_steps import BuildStep, from_config
from .cli import cli
from .conf import config


def _require_config():
    """Return the loaded project config or abort if we're not inside a project."""
    if config is None:
        utils.echo_fatal("No project.json found - please check if you are in the right folder.")
    return config


def _parse_env(pairs: t.Sequence[str]) -> dict[str, str]:
    """Parse repeated ``-e KEY=VALUE`` options into a dict.

    Aborts via ``echo_fatal`` on a missing ``=`` or an empty key; an empty
    value (``KEY=``) is allowed. On a duplicate key the last one wins.
    """
    result: dict[str, str] = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep or not key:
            utils.echo_fatal(f"Invalid --env entry {pair!r}, expected KEY=VALUE")
        result[key] = value
    return result


def _load(profile: str) -> tuple[dict, dict[str, BuildStep]]:
    """Resolve `profile` and parse its `builds` section into BuildStep objects."""
    conf = _require_config().get_profile(profile)
    steps: dict[str, BuildStep] = {}
    for name, cfg in conf.get("builds", {}).items():
        try:
            steps[name] = from_config(name, cfg)
        except ValueError as exc:
            utils.echo_fatal(str(exc))
    return conf, steps


@cli.group()
def build():
    """Build deploy artifacts (npm bundles, exec build steps) for a ViUR project."""


@build.command()
@click.option("-p", "--profile", default="default", help="Profile from project.json.")
@click.option("-v", "--verbose", is_flag=True, default=False,
              help="Echo every command, working directory and env override before running it.")
@click.option("-e", "--env", "env_pairs", multiple=True, metavar="KEY=VALUE",
              help="Set an environment variable for every build step (repeatable).")
def release(profile: str, verbose: bool, env_pairs: tuple[str, ...]) -> None:
    """Build every entry in the profile's `builds` section, in declaration order.

    Only viur-cli flags are accepted here. To pass arbitrary arguments to a build
    tool, target a single build: `viur build app <name> -- <args…>`.
    """
    conf, steps = _load(profile)
    extra_env = _parse_env(env_pairs)

    utils.echo_info("building started...")
    for step in steps.values():
        utils.echo_info(f"- {step.kind} {step.name}")
        step.run(conf, extra_env=extra_env, verbose=verbose)
    utils.echo_info("building finished!")


@build.command(context_settings={"ignore_unknown_options": True})
@click.argument("appname")
@click.option("-p", "--profile", default="default", help="Profile from project.json.")
@click.option("-v", "--verbose", is_flag=True, default=False,
              help="Echo the command, working directory and env override before running it.")
@click.option("-e", "--env", "env_pairs", multiple=True, metavar="KEY=VALUE",
              help="Set an environment variable for this build (repeatable).")
@click.argument("additional_args", nargs=-1, type=click.UNPROCESSED)
def app(
    appname: str,
    profile: str,
    verbose: bool,
    env_pairs: tuple[str, ...],
    additional_args: tuple[str, ...],
) -> None:
    """Build a single application (APPNAME) from the profile's `builds` section.

    Extra arguments after `--` are passed through to the build tool, e.g.
    `viur build app ui -- --mode staging` runs `npm run build -- --mode staging`.
    """
    conf, steps = _load(profile)
    if (step := steps.get(appname)) is None:
        utils.echo_fatal(f"""{appname=} must be one of these options: {", ".join(steps)}""")

    utils.echo_info("building started...")
    utils.echo_info(f"- {step.kind} {step.name}")
    step.run(conf, extra_args=additional_args, extra_env=_parse_env(env_pairs), verbose=verbose)
    utils.echo_info("building finished!")


@build.command()
@click.argument("target", default="")
@click.option("-p", "--profile", default="default", help="Profile from project.json.")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Verbose output.")
def clean(target: str, profile: str, verbose: bool) -> None:
    """Drop build artifacts for one application (TARGET) or for all builds in the profile."""
    conf, steps = _load(profile)

    if target:
        if (step := steps.get(target)) is None:
            utils.echo_fatal(f"""{target=} must be one of these options: {", ".join(steps)}""")
        steps = {target: step}

    utils.echo_info("clean started...")
    for step in steps.values():
        utils.echo_info(f"- cleaning {step.kind} {step.name}")
        step.clean(conf, verbose=verbose)
    utils.echo_info("clean finished!")
