import click, os, json
from . import cli, echoError, getConfig, echoInfo


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("name", default='develop')
@click.argument("additional_args", nargs=-1)
def deploy(name, additional_args):
    """deploy your application"""
    projectConfig = getConfig()

    if name not in projectConfig:
        echoError(f"{name} is not a valid config name.")
        return

    conf = projectConfig["default"].copy()
    conf.update(projectConfig[name])

    # rebuild requirements.txt
    createReq()

    os.system(
        f'gcloud app deploy --project={conf["application_name"]} --version={conf["version"]} --no-promote {" ".join(additional_args)} {conf["distribution_folder"]}')


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("name", default='develop')
@click.argument("additional_args", nargs=-1)
def index(name, additional_args):
    """update your application index"""
    projectConfig = getConfig()

    if name not in projectConfig:
        echoError(f"{name} is not a valid config name.")
        return

    conf = projectConfig["default"].copy()
    conf.update(projectConfig[name])

    # rebuild requirements.txt
    createReq()

    os.system(
        f'gcloud app deploy --project={conf["application_name"]} {" ".join(additional_args)} {conf["distribution_folder"]}/index.yaml')


@cli.command()
def check():
    """check project"""
    pass


def createReq():
    """
    load projects pipenv and build a requirements.txt

    cores requirements.txt cant be validated currently, because of the core does not provide a feature for that
    """

    projectConfig = getConfig()
    distFolder = projectConfig["default"]["distribution_folder"]

    if click.confirm(f"Do you want to regenerate the requirements.txt located in the {distFolder}?"):
        os.system(f"pipfile2req  --hashes > {distFolder}/requirements.txt")
        echoInfo("requirements.txt successfully generated")
