import click
import os
from .conf import *
from .version import __version__




@click.group(invoke_without_command=True, no_args_is_help=True)
@click.version_option(__version__)
@click.pass_context
def cli(ctx):
    """Info output"""
    if ctx.invoked_subcommand not in ["init","create"]:
        load_config()
    fetch_core_version()


@cli.command()
@click.argument("action", type=click.Choice(['add', 'remove', 'list', 'addFlare', 'scanNpm']))
def project(action):
    """manage project.json and generate if missing"""
    projectConfig = get_config()
    if action == "add":
        add_to_config()
    elif action == "addFlare":
        _projectconf = add_to_flare_config(projectConfig)
        write_config(_projectconf)
    elif action == "scanNpm":
        _projectconf = add_npm_apps()
        write_config(_projectconf)
    elif action == "remove":
        remove_from_config()
    elif action == "list":
        click.echo(click.style(json.dumps(projectConfig, indent=4, sort_keys=True), fg="cyan"))
