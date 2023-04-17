import click, os, zipfile, shutil, urllib, json
from . import cli, get_config, echo_error, write_config
from urllib.request import urlretrieve
from . import cli, echo_error, utils, conf


@cli.group()
def build():
    """Build VIUR project"""

@build.command(context_settings={"ignore_unknown_options": True})
@click.argument("name", default='develop')
@click.argument("additional_args", nargs=-1)
def release(name, additional_args):
    """create a release build"""

    utils.echo_info("building started...")
    projectConfig = conf.get_config()

    if not os.popen("pyenv versions").read():
        echo_error(f"pyenv not found!")
        return

    if name not in projectConfig:
        echo_error(f"{name} is not a valid config name.")
        return

    cfg = projectConfig["default"].copy()
    cfg.update(projectConfig[name])


    if builds_cfg := cfg.get("builds"):

        # build all flare apps
        if flare_apps := [k for k,v in builds_cfg.items() if builds_cfg[k]["kind"] == "flare"]:
            # we have atlease 1 flare app
            # Ensure for local pyodide.
            pyodide_version = cfg.get("pyodide", conf.DEFAULT_PYODIDE_VERSION)
            utils.echo_info(f"- Ensuring Pyodide {pyodide_version} local install")

            os.system(f'get-pyodide -t {cfg["distribution_folder"]}/pyodide -v v{pyodide_version}')

            if "debug" in additional_args:
                flare_build_type = "debug"
                flare_build_env = ""
            else:
                flare_build_type = "release"
                flare_build_env = "pyenv exec"

                #enforce python 3.9.5
                if "3.9.5" not in os.popen("pyenv versions").read():
                    os.system(f'pyenv install 3.9.5')
                os.system("pyenv local 3.9.5")

            for name in flare_apps:
                utils.echo_info(f"- Building {flare_build_type} {name}")
                os.system(f'{flare_build_env} viur flare {flare_build_type} {name}')

            if flare_build_type == "release":
                os.system("pyenv local system")

        # build all npm apps
        if npm_apps := [k for k,v in builds_cfg.items() if builds_cfg[k]["kind"] == "npm"]:
            for name in npm_apps:
                utils.echo_info(f"- Building {name}")
                os.system(f'cd {cfg["sources_folder"]}{builds_cfg[name]["source"]} && npm install && npm run {builds_cfg[name]["command"]}')
        # build all scripts
        if script_apps := [k for k, v in builds_cfg.items() if builds_cfg[k]["kind"] == "exec"]:
            for name in script_apps:
                utils.echo_info(f"- Building {name}")
                os.system(builds_cfg[name]["command"])
    utils.echo_info("building finished!")

@build.command(context_settings={"ignore_unknown_options": True})
@click.argument("appname", default="")
@click.argument("additional_args", nargs=-1)
def app(appname, additional_args):
    """create a release build"""
    valid_apps = conf.get_config()["default"]["builds"].keys()
    if not appname or appname not in valid_apps:
        echo_error("appname musst be one of these options")
        echo_error(", ".join(valid_apps))
        return

    utils.echo_info("building started...")
    projectConfig = conf.get_config()

    if not os.popen("pyenv versions").read():
        echo_error(f"pyenv not found!")
        return

    cfg = projectConfig["default"].copy()

    builds_cfg = cfg.get("builds").get(appname)

    if builds_cfg["kind"] == "flare":
        pyodide_version = cfg.get("pyodide", conf.DEFAULT_PYODIDE_VERSION)
        utils.echo_info(f"- Ensuring Pyodide {pyodide_version} local install")

        os.system(f'get-pyodide -t {cfg["distribution_folder"]}/pyodide -v v{pyodide_version}')

        if "debug" in additional_args:
            flare_build_type = "debug"
            flare_build_env = ""
        else:
            flare_build_type = "release"
            flare_build_env = "pyenv exec"

            # enforce python 3.9.5
            if "3.9.5" not in os.popen("pyenv versions").read():
                os.system(f'pyenv install 3.9.5')
            os.system("pyenv local 3.9.5")

        utils.echo_info(f"- Building Flare: {flare_build_type} {appname}")
        os.system(f'{flare_build_env} viur flare {flare_build_type} {appname}')

        if flare_build_type == "release":
            os.system("pyenv local system")
    elif builds_cfg["kind"] == "npm":
        utils.echo_info(f"- Building NPM: {appname}")
        os.system(
            f'cd {cfg["sources_folder"]}{builds_cfg["source"]} && npm install && npm run {builds_cfg["command"]}')
    elif builds_cfg["kind"] == "exec":
        utils.echo_info(f"- Building Script: {appname}")
        os.system(builds_cfg["command"])

    utils.echo_info("building finished!")