"""
Performs build steps configured within the project, or creates any necessary steps for a project deployment build.
"""

import click, os, zipfile, shutil, urllib, json
from urllib.request import urlretrieve
from . import cli, conf, utils, get_config, write_config


def _build(cfg, name, build_cfg, additional_args):
    """Internal function to perform steps required for a given build configuration.

    :param cfg: The project configuration (default, or project-specific)
    :param name: Name of the app to build.
    :param build_cfg: The build-cfg for the specified app.
    :param additional_args: List of additional arguments.
    """
    utils.echo_info(f"""- {build_cfg["kind"]} {name}""")

    match build_cfg["kind"]:
        case "flare":
            # Ensure for local pyodide, if configured!
            if pyodide_version := cfg.get("pyodide"):
                utils.echo_info(f"- Ensuring Pyodide {pyodide_version} local install")
                utils.system(f'get-pyodide -t {cfg["distribution_folder"]}/pyodide -v v{pyodide_version}')

            if "debug" in additional_args:
                flare_build_type = "debug"
                flare_build_env = ""
            else:
                flare_build_type = "release"
                flare_build_env = "pyenv exec"

                # enforce python 3.9.5
                # FIXME: This is highly obsolete...
                if "3.9.5" not in os.popen("pyenv versions").read():
                    utils.system(f'pyenv install 3.9.5')
                utils.system("pyenv local 3.9.5")

            utils.echo_info(f"- Building Flare: {flare_build_type} {name}")
            utils.system(f'{flare_build_env} viur flare {flare_build_type} {name}')

            if flare_build_type == "release":
                utils.system("pyenv local system")

        case "npm":
            utils.system(
                " && ".join(
                    (
                        f'cd {os.path.join(cfg["sources_folder"], build_cfg["source"])}',
                        "npm install",
                        f'npm run {build_cfg["command"]}'
                    )
                )
            )

        case "exec":
            utils.system(build_cfg["command"])

        case other:
            utils.echo_fatal(f"Unknown build kind {other!r}")


@cli.group()
def build():
    """Build VIUR project or specific apps."""

@build.command(context_settings={"ignore_unknown_options": True})
@click.argument("name", default='develop')
@click.argument("additional_args", nargs=-1)
def release(name, additional_args):
    """Build of all relevant apps to deploy this project."""

    projectConfig = conf.get_config()

    if name not in projectConfig:
        utils.echo_fatal(f"{name} is not a valid config name.")

    cfg = projectConfig["default"].copy()
    cfg.update(projectConfig[name])

    utils.echo_info("building started...")

    for build_name, build_cfg in cfg.get("builds", {}).items():
        _build(cfg, build_name, build_cfg, additional_args)

    utils.echo_info("building finished!")

@build.command(context_settings={"ignore_unknown_options": True})
@click.argument("appname", default="")
@click.argument("additional_args", nargs=-1)
def app(appname, additional_args):
    """Build specific app."""

    projectConfig = conf.get_config()

    cfg = projectConfig["default"].copy()

    if not (build_cfg := cfg.get("builds").get(appname)):
        utils.echo_fatal(f"""{appname=} must be one of these options: {", ".join(cfg["builds"].keys())}""")

    utils.echo_info("building started...")
    _build(cfg, appname, build_cfg, additional_args)
    utils.echo_info("building finished!")
