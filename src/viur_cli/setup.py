import click
import os
from .conf import *
from .cli import cli
from .utils import *

@cli.command()
@click.argument("name")
@click.pass_context
def create(ctx, name):
    """create a new ViUR project"""
    if os.path.exists(f'./{name}'):
        echo_error(f'"{name}" Folder exists. Please use a different name or remove this folder ./{name}')
        return

    # fetch base project
    os.system(
        f'git clone https://github.com/viur-framework/viur-base.git {name}')
    project_json_path = f'./{name}/project.json'

    # collect project info
    projectConfig = load_config(path=project_json_path)
    appname = projectConfig["develop"]['application_name']

    # run clean-base
    os.system(f'cd ./{name} && python3 clean-base.py -A={appname}')

    # run gcloud config
    if click.confirm(f'Do you want to configure "{appname}" as a new gcloud project?'):
        os.system(f'cd ./{name} && ./viur-gcloud-setup.sh {appname}')
