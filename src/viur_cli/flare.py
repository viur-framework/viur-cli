import click, os
from . import cli, echoError, getConfig


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("name")
@click.argument("action")
@click.argument("additional_args", nargs=-1)
def flare(action, name, additional_args):
    """build or watch a flare fontend"""
    projectConfig = getConfig()
    additional_args = list(additional_args)

    if action == "release":
        additional_args = ["-mzc"]
    elif action == "debug":
        pass
    elif action == "watch":
        additional_args = ["-w"]

    if name not in projectConfig["default"]["flare"]:
        echoError(f"{name} is not a valid flare app name.")
        return

    conf = projectConfig["default"].copy()

    os.system(
        f'flare -n={name} -s={conf["flare"][name]["source"]} -t={conf["flare"][name]["target"]} {" ".join(additional_args)}')
