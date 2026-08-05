"""Build pipeline for ViUR projects: orchestrates npm and exec build steps."""

import click
import os
from .conf import config
from .cli import cli
from . import utils


def _build(conf, name, build_cfg, additional_args):
    """Run a single build entry from a profile's `builds` section.

    Args:
        conf: Resolved profile configuration.
        name: The build entry's key (used only for log output).
        build_cfg: The build entry itself. Required keys depend on
            ``kind``:

            * ``kind == "npm"`` — needs ``source`` (relative to
              ``conf['sources_folder']``) and ``command`` (the npm
              script name to run).
            * ``kind == "exec"`` — needs ``command`` (a shell string
              executed verbatim).

        additional_args: Extra args passed to the build callable.
            Currently ignored by both kinds — kept for forward
            compatibility.

    Aborts (via ``echo_fatal``) on an unknown ``kind``.
    """
    utils.echo_info(f"""- {build_cfg["kind"]} {name}""")
    match build_cfg["kind"]:
        case "npm":
            utils.system(
                " && ".join(
                    (
                        f'cd {os.path.join(conf["sources_folder"], build_cfg["source"])}',
                        "npm install",
                        f'npm run {build_cfg["command"]}'
                    )
                )
            )

        case "exec":
            utils.system(build_cfg["command"])

        case other:
            utils.echo_fatal(f"Unknown build kind {other!r}")


def _clean(conf, name, build_cfg):
    """Drop generated artifacts for a single build entry.

    Args:
        conf: Resolved profile configuration.
        name: The build entry's key (used only for log output).
        build_cfg: The build entry. Recognized keys:

            * ``target`` (npm only) — deleted under
              ``conf['distribution_folder']``
            * ``source`` (npm only) — its ``node_modules`` is dropped
            * ``clean`` (any kind) — explicit shell command run after
              the kind-specific cleanup

    Aborts on unknown ``kind``.
    """
    utils.echo_info(f"""- cleaning {build_cfg["kind"]} {name}""")

    match build_cfg["kind"]:
        # for npm, drop the target folder and node_modules (npm)
        case "npm":
            if target_dir := build_cfg.get("target"):
                target_dir = os.path.join(conf["distribution_folder"], target_dir)
                utils.echo_info(f"  - dropping {target_dir}")
                utils.rmdir(target_dir)

            if build_cfg["kind"] == "npm":
                # todo: Later, call "npm run clean" or a similar command when it exists

                node_modules = os.path.join(conf["sources_folder"], build_cfg["source"], "node_modules")
                utils.echo_info(f"  - dropping {node_modules}")
                utils.rmdir(os.path.join(node_modules))

        case "exec":
            pass

        case other:
            utils.echo_fatal(f"Unknown build kind {other!r}")

    # Always execute explicit "clean" command if provided
    if clean_cmd := build_cfg.get("clean"):
        utils.echo_info(f"  - executing {clean_cmd=}")
        utils.system(clean_cmd)


@cli.group()
def build():
    """Build deploy artifacts (npm bundles, exec build steps) for a ViUR project."""


@build.command(context_settings={"ignore_unknown_options": True})
@click.argument("profile", default='default')
@click.argument("additional_args", nargs=-1)
def release(profile, additional_args):
    """Build every entry in the profile's `builds` section, in declaration order."""
    conf = config.get_profile(profile)
    utils.echo_info("building started...")

    for build_name, build_cfg in conf.get("builds", {}).items():
        _build(conf, build_name, build_cfg, additional_args)

    utils.echo_info("building finished!")


@build.command(context_settings={"ignore_unknown_options": True})
@click.argument("appname")
@click.argument("additional_args", nargs=-1)
@click.argument("profile", default="default")
def app(appname, profile, additional_args):
    """Build a single application from the profile's `builds` section."""

    conf = config.get_profile(profile)

    if not (build_cfg := conf.get("builds").get(appname)):
        utils.echo_fatal(f"""{appname=} must be one of these options: {", ".join(conf["builds"].keys())}""")

    utils.echo_info("building started...")
    _build(conf, appname, build_cfg, additional_args)
    utils.echo_info("building finished!")


@build.command
@click.argument("target", default="")
@click.argument("profile", default="default")
def clean(target, profile):
    """Drop build artifacts for one application (TARGET) or for all builds in the profile."""

    conf = config.get_profile(profile)

    builds = conf.get("builds", {})
    if target:
        if not (build_cfg := builds.get(target)):
            utils.echo_fatal(f"""{target=} must be one of these options: {", ".join(conf["builds"].keys())}""")

        builds = {target: build_cfg}

    utils.echo_info("clean started...")

    for build_name, build_cfg in builds.items():
        _clean(conf, build_name, build_cfg)

    utils.echo_info("clean finished!")
