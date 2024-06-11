import os
import re
import subprocess
import tempfile
import click
from .conf import *
from .version import __version__, MINIMAL_PIPENV
import semver
import pprint


def has_reached_code():
    """Checks if a specific piece of code has been reached before."""
    temp_file = tempfile.NamedTemporaryFile(mode='w+t', delete=False, prefix='viur_cli_', dir='/tmp')
    unique_filename = os.path.basename(re.sub(r'[^\w\s]', '_', os.getcwd()).strip())
    temp_file.name = os.path.join(os.path.dirname(temp_file.name), unique_filename)
    print(f"Temporary file created: {temp_file.name}")
    # Write content to the temporary file
    temp_file.write("This is a temp file created by viur-cli!")
    echo_error("I AM HERE")

    # Check if the file already exists

    try:
        with open(temp_file.name, 'r') as f:
            f.read()  # Attempt to read, any content means reached before
            return True
    except FileNotFoundError:
        pass  # File not found, haven't reached this point yet

    # No existing file, create it to mark reaching this point
    with open(temp_file.name, 'w') as f:
        f.write("Reached code")  # Write some content
    return False


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

    if not has_reached_code():
        checkables = ["viur-core", "viur-cli"]
        for checkable in checkables:
            check_version(checkable)


def get_package_version(name):
    process = subprocess.run(["pip", "show", name], capture_output=True, check=True)
    output = process.stdout.decode("utf-8")
    for line in output.splitlines():
        if line.startswith("Version:"):
            return line.split()[1].strip()


def get_latest_version(name):
    all_versions = subprocess.run(
        ["pip", "index", "versions", name], capture_output=True, check=True
    ).stdout.decode()
    latest_version = all_versions.split("LATEST")[1].split(":")[1].strip()
    return latest_version


def update_pipfile(name, version):
    command = f"{name}=={version}"
    subprocess.run(["pipenv", "install", command], capture_output=True, check=True).stdout.decode()


def check_version(name):
    echo_positive("I AM CALLED")
    actual = get_package_version(name)
    latest = get_latest_version(name)

    if actual != latest:
        echo_info(f"Installed Version: {actual}")
        echo_info(f"Latest Version: {latest}")
        if click.confirm(f"It seems like you have not installed the latest {name} version.\n "
                         f"Do you want to update it now?", default=True):
            update_pipfile(name, latest)
            return


@cli.command()
@click.argument("action", type=click.Choice(['list']))
@click.argument("profile", default="default")
def project(action, profile):
    """List your project.json Configuration File"""
    project_config = config.get_profile(profile)
    if action == "list":
        echo_info(f"These are the Settings for {profile} profile")
        pprint.pprint(project_config)
