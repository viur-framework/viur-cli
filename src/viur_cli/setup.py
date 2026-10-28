import os
import subprocess
import click
from .cli import cli
from .utils import *


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("name")
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def create(ctx, name, args):
    """Clone viur-base into ./NAME and run its clean-base.py setup wizard.

    ARGS are passed unchanged to ``clean-base.py`` (e.g. ``--frontend spa``);
    use ``viur create NAME -- --help`` to list them.

    Optionally chains into ``./viur-gcloud-setup.sh NAME`` if confirmed,
    so the project is wired to a fresh GCP project in one shot.
    """
    if os.path.exists(f'./{name}'):
        echo_error(f'"{name}" Folder already exists. Please use a different name or remove this folder ./{name}')
        return

    # fetch base project
    git_clonne_cmd = ['git', 'clone', f'https://github.com/viur-framework/viur-base.git', name]
    subprocess.run(git_clonne_cmd, check=True)

    wdir = f"{os.getcwd()}/{name}"

    # Run clean-base.py
    clean_base_cmd = ['python3', 'clean-base.py', '-A', name, *args]
    try:
        subprocess.run(clean_base_cmd, check=True, cwd=wdir)
    except subprocess.CalledProcessError:
        echo_error(f'clean-base.py did not complete, ./{name} is not set up. Remove it and run `viur create` again.')
        return

    # Run gcloud config (if confirmed)
    if click.confirm(f'Do you want to configure "{name}" as a new gcloud project?'):
        gcloud_setup_cmd = ['./viur-gcloud-setup.sh', name]
        subprocess.run(gcloud_setup_cmd, check=True, cwd=wdir)
