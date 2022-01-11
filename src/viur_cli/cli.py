import click
import os
from .conf import *
from .version import __version__


@click.group(invoke_without_command=True, no_args_is_help=True)
@click.version_option(__version__)
def cli():
    """Info output"""
    load_config()
    fetch_core_version()


@cli.command()
@click.argument("action", type=click.Choice(['add', 'remove', 'list', 'addFlare']))
def project(action):
    """manage project.json and generate if missing"""
    projectConfig = get_config()
    if action == "add":
        if projectConfig:
        	add_to_config(click.prompt('name'), click.prompt('application name'), click.prompt('develop version name'))
    elif action == "addFlare":
        if "default" not in projectConfig:
            raise click.ClickException(click.style("default entry is missing", fg="red"))
        _projectconf = add_to_flare_config(projectConfig, click.prompt('name'), click.prompt('source'), click.prompt('target'))
        write_config(_projectconf)
    elif action == "remove":
        remove_from_config(click.prompt('name'))
    elif action == "list":
        click.echo(click.style(json.dumps(projectConfig, indent=4, sort_keys=True), fg="cyan"))
