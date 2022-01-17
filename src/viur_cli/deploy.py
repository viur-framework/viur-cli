import click, os, json
from . import cli, echo_error, get_config, echo_info
from typing import List

@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(['app', 'index', 'cron', 'queue']))
@click.argument("name", default='develop')
@click.argument("additional_args", nargs=-1)
def deploy(action: str, name: str, additional_args: List[str]):
    """deploy gcloud app or different yaml files"""
    projectConfig = get_config()

    if name not in projectConfig:
        echo_error(f"{name} is not a valid config name.")
        return

    conf = projectConfig["default"].copy()
    conf.update(projectConfig[name])

    if action == "app":
        # rebuild requirements.txt
        projectConfig = get_config()
        distFolder = projectConfig["default"]["distribution_folder"]
        create_req(regenerate=click.confirm(f"Do you want to regenerate the requirements.txt located in the {distFolder}?"))

        os.system(
            f'gcloud app deploy --project={conf["application_name"]} --version={conf["version"]} --no-promote {" ".join(additional_args)} {conf["distribution_folder"]}')
    else:
        if action not in ["index", "queue", "cron"]:
            echo_error(f"{action} is not a valid action. Valid is app, index, queue, cron")

        os.system(
            f'gcloud app deploy --project={conf["application_name"]} {" ".join(additional_args)} {conf["distribution_folder"]}/{action}.yaml')


def create_req(regenerate: bool):
    """
    load projects pipenv and build a requirements.txt

    cores requirements.txt cant be validated currently, because of the core does not provide a feature for that
    """


    projectConfig = get_config()
    distFolder = projectConfig["default"]["distribution_folder"]

    if regenerate:
        os.system(f"pipfile2req  --hashes > {distFolder}/requirements.txt")
        echo_info("requirements.txt successfully generated")
