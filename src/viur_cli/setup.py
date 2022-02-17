import click
import os
from .conf import *
from .cli import cli
from .utils import *


@cli.command()
def init():
    """initialize project.json"""

    print("Test")
    projectConfig = get_config()
    try:
        f = open(projectConfigFilePath)
        if click.confirm("project.json already exists, do you want to delete it and create a new project.json?"):
            os.remove(projectConfigFilePath)
            create_new_config()
    except:

        if not projectConfig:
            if click.confirm("Do you want to create a new project.json file?"):
                create_new_config()

def create(name: str, configure_gcloud_project: bool = False) -> None:
    """create a new ViUR project"""
    if os.path.exists(f'./{name}'):
        echo_error(f'"{name}" Folder exists. Please use a different name or remove this folder ./{name}')
        return

    # fetch base project
    os.system(
        f'git clone https://github.com/viur-framework/viur-base.git {name}')
    project_json_path = f'./{name}/project.json'

    # collect project info
    #create_new_config_extended(project_json_path)
    projectConfig = load_config(path=project_json_path)
    appname = projectConfig["develop"]['application_name']

    # run clean-base
    os.system(f'cd ./{name} && python3 clean-base.py -A={appname}')

    if configure_gcloud_project:
        os.system(f'cd ./{name} && ./viur-gcloud-setup.sh {appname}')

@cli.command(name="create")
@click.argument("name")
@click.pass_context
def _create(ctx: click.Context, name: str):
    """create a new ViUR project"""
    project_json_path = f'./{name}/project.json'
    projectConfig = load_config(path=project_json_path)
    app_name = projectConfig["develop"]['application_name']

    create(name, click.confirm(f'Do you want to configure "{app_name}" as a new gcloud project?'))
