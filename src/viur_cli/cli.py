import re
import subprocess
import click
from .conf import *
from .version import __version__
from .version import MINIMAL_PIPENV
import semver
import pprint


@click.group(invoke_without_command=True, no_args_is_help=True,
             context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__)
@click.pass_context
def cli(ctx):
    """
    Command-line interface for managing project configuration and information.

    The viur-cli provides a set of commands to manage your project's configuration in the 'project.json'.
     It also offers commands to view and modify project information.

    Note:

        - Use the `--version` option to display the CLI tool's version.

        - Run the 'project' command to manage 'project.json' and project configuration settings.
    """

    # Get the systems pipenv Version Number
    pipenv_version = subprocess.check_output(['pipenv', '--version']).decode("utf-8")
    version_pattern = r'\b(\d+\.\d+\.\d+)\b'
    match = re.search(version_pattern, pipenv_version)
    sys_pipenv = match.group(1)

    # sys kleiner min
    if semver.compare(sys_pipenv, MINIMAL_PIPENV) < 0:
        echo_warning(
            f"Your pipenv Version does not match the recommended pipenv version. \n"
            f"This mismatch may cause Errors, please consider updating your Systems pipenv version \n"
            f"Your Version: {sys_pipenv}\n"
            f"Recommended Version: {MINIMAL_PIPENV}"
        )


@cli.command()
@click.argument("action", type=click.Choice(['list']))
@click.argument("profile", default="default")
def project(action, profile):
    """List your project.json Configuration File"""
    project_config = config.get_profile(profile)
    if action == "list":
        echo_info(f"These are the Settings for {profile} profile")
        pprint.pprint(project_config)
