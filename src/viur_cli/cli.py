import re
import subprocess
from .conf import *
from .version import __version__
from .version import MINIMAL_PIPENV
import semver


@click.group(invoke_without_command=True,
             no_args_is_help=True,
             context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__)
@click.pass_context
def cli(ctx):
    """
    Command-line interface for managing project configuration and information.

    The viur-cli provides a set of commands to manage your project's configuration in the 'project.json'
    if missing. It also offers commands to view and modify project information.

    Usage:
    ```
    viur [OPTIONS] COMMAND [ARGS]...
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

    # Get the systems pipenv Version Number
    foobar = subprocess.check_output(['pipenv', '--version']).decode("utf-8")
    version_pattern = r'\b(\d+\.\d+\.\d+)\b'
    match = re.search(version_pattern, foobar)
    sys_pipenv = match.group(1)

    # sys kleiner min
    if semver.compare(sys_pipenv, MINIMAL_PIPENV) < 0:
        echo_warning(
            f"Your pipenv Version does not match the recommended pipenv version. \n"
            f"This mismatch may cause Errors, please consider to update your Systems pipenv version \n"
            f"Your Version: {sys_pipenv}\n"
            f"Recommended Version: {MINIMAL_PIPENV}"
        )

    if ctx.invoked_subcommand not in ["init", "create"]:
        load_config()
    fetch_core_version()


@cli.command()
@click.argument("action", type=click.Choice(['add', 'remove', 'list', 'scanNpm']))
def project(action):
    """
    Manage project.json and generate if missing.

    This command allows you to manage the 'project.json' file and associated project configuration settings. You can
    add, remove, list, and modify project information using this command.

    :param action: str
        The action to perform on 'project.json' and project configuration. It can be one of the following:
        - 'add': Add project information to 'project.json.
        - 'remove': Remove project information from 'project.json.'
        - 'list': List project information.

    Example Usage:
    ```shell
    viur-cli project add
    viur-cli project remove
    viur-cli project list
    ```

    Note:
    - When using the 'add' actions, you can provide additional information as needed.
    - The 'list' action displays project information in a formatted JSON format.

    :return: None
    """
    project_config = get_config()
    if action == "add":
        add_to_config()
    elif action == "remove":
        remove_from_config()
        click.echo(click.style(json.dumps(project_config, indent=4, sort_keys=True), fg="cyan"))
    elif action == "list":
        pass
