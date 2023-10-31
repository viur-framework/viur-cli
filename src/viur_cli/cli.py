import click
import os
from .conf import *
from .version import __version__


@click.group(invoke_without_command=True, no_args_is_help=True)
@click.version_option(__version__)
@click.pass_context
def cli(ctx):
    """
    Command-line interface for managing project configuration and information.

    The viur-cli provides a set of commands to manage your project's configuration in the 'project.json'
    if missing. It also offers commands to view and modify project information.

    Usage:
    ```
    myproject-cli [OPTIONS] COMMAND [ARGS]...
    ```

    Options:
      -h, --help      Show this message and exit.
      --version       Show the CLI tool's version.

    Commands:
      project         Manage project.json and generate if missing.

    Note:
    - Use the `--version` option to display the CLI tool's version.
    - Run the 'project' command to manage 'project.json' and project configuration settings.

    :return: None
    """

    if ctx.invoked_subcommand not in ["init", "create"]:
        load_config()
    fetch_core_version()


@cli.command()
@click.argument("action", type=click.Choice(['add', 'remove', 'list', 'addFlare', 'scanNpm']))
def project(action):
    """
    Manage project.json and generate if missing.

    This command allows you to manage the 'project.json' file and associated project configuration settings. You can
    add, remove, list, and modify project information using this command.

    :param action: str
        The action to perform on 'project.json' and project configuration. It can be one of the following:
        - 'add': Add project information to 'project.json.'
        - 'addFlare': Add project information to Flare configuration.
        - 'remove': Remove project information from 'project.json.'
        - 'list': List project information.

    Example Usage:
    ```shell
    viur-cli project add
    viur-cli project addFlare
    viur-cli project remove
    viur-cli project list
    ```

    Note:
    - When using the 'add' or 'addFlare' actions, you can provide additional information as needed.
    - The 'list' action displays project information in a formatted JSON format.

    :return: None
    """
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
