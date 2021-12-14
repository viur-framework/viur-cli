import click
import os
from .conf import *
from .version import __version__


@click.group(invoke_without_command=True)
@click.option("-v", "--version", is_flag=True)
def cli(version):
    """Info output"""
    if version:
        click.echo(f"ViUR-CLI v{__version__}")
        return 0
    click.echo("Welcome to ViUR-CLI")

    load_config()
    fetch_core_version()


@cli.command()
@click.argument("action", type=click.Choice(['add', 'remove', 'list', 'addFlare']))
def project(action):
    """manage project.json and generate if missing"""
    projectConfig = get_config()
    if action == "add":
        add_to_config()
    elif action == "addFlare":
        _projectconf = add_to_flare_config(projectConfig)
        write_config(_projectconf)
    elif action == "remove":
        remove_from_config()
    elif action == "list":
        click.echo(click.style(json.dumps(projectConfig, indent=4, sort_keys=True), fg="cyan"))
