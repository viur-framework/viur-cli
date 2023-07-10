import click, os, shutil
from . import cli, echo_error, get_config


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(['release', 'debug', 'watch']))
@click.argument("name", default="")
@click.argument("additional_args", nargs=-1)
def flare(action, name, additional_args):
    """build or watch a flare frontend"""
    projectConfig = get_config()
    additional_args = list(additional_args)

    if action == "release":
        additional_args = ["-mzc"]
    elif action == "debug":
        pass
    elif action == "watch":
        additional_args = ["-w"]

    if not name:
        if len(projectConfig["default"]["builds"]) == 0:
            echo_error(f"No flare app configured")
        else:
            flare_apps = [k for k,v in projectConfig["default"]["builds"].items() if v["kind"] == "flare"]
            if not flare_apps:
                echo_error(f"No flare app configured")

            name = flare_apps[0]

    elif name not in projectConfig["default"]["builds"] or projectConfig["default"]["builds"][name]["kind"]!="flare":
        echo_error(f"{name} is not a valid flare app name.")
        return

    conf = projectConfig["default"].copy()

    os.system(
        f'flare -n={name} -s={conf["builds"][name]["source"]} -t={conf["builds"][name]["target"]} {" ".join(additional_args)}')
