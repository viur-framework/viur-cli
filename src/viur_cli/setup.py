import click
import os
from .conf import config
from .cli import cli
from .utils import *


@cli.command()
@click.argument("name")
@click.pass_context
def create(ctx, name):
    """
    Create a new ViUR project.

    The 'create' command allows you to create a new ViUR project by cloning the ViUR base project and configuring it.
    You can specify the name of the new project as the 'name' argument.

    The 'create' command performs the following steps:

        1. Clones the ViUR base project from the official GitHub repository.

        2. Configures the new project by running 'clean-base.py'.

        3. Optionally configures the project as a new gcloud project (if confirmed).

    Note:

        - This command initializes the new ViUR project based on the ViUR base project.

        - Make sure to provide a unique project name to avoid conflicts with existing folders.

    """
    if os.path.exists(f'./{name}'):
        echo_error(f'"{name}" Folder exists. Please use a different name or remove this folder ./{name}')
        return

    # fetch base project
    os.system(
        f'git clone https://github.com/viur-framework/viur-base.git {name}')
    project_json_path = f'./{name}/project.json'

    # collect project info
    conf = config.get_profile("default")
    appname = conf['application_name']

    # run clean-base
    os.system(f'cd ./{name} && python3 clean-base.py -A={appname}')

    # run gcloud config
    if click.confirm(f'Do you want to configure "{appname}" as a new gcloud project?'):
        os.system(f'cd ./{name} && ./viur-gcloud-setup.sh {appname}')
