import click
import os

from . import cli


@cli.group()
def tool():
    """
    Run different ViUR-related scripts.

    The 'tool' group allows you to execute various ViUR-related scripts that help with tasks such as project porting,
    Pyodide installation, and SSL certificate fixes.

    Available Commands:

        - 'pyodide': Run the get_pyodide command.

        - 'ssl_fix': SSL certificate fix for macOS.
    """


@tool.command()
@click.option('--version', '-v')
@click.option('--package', '-p')
@click.option('--target', '-t')
@click.option('--help', '-h')
def pyodide(additional_args, version, package, target, help):
    """
    The 'pyodide' command allows you to run the 'get_pyodide' command for Pyodide installation.

    :param additional_args: tuple
        Additional arguments to pass to the 'get_pyodide' command.
    :param version: str, optional
        Specify the version of Pyodide.
    :param package: str, optional
        Specify the package for Pyodide.
    :param target: str, optional
        Specify the target for Pyodide.
    :param help: bool, optional
        Display help for the 'get_pyodide' command.

    Example Usage:
    ```
    viur tool pyodide -v 0.19.1 -p mypackage -t mytarget
    ```

    :return: None
    """
    command = "get-pyodide"
    if help:
        os.system("get-pyodide -h")

    if version:
        command += f" -v {version}"

    if package:
        command += f" -p {package}"

    if target:
        command += f" -t {target}"

    os.system(command)


@tool.command()
def ssl_fix():
    """
    SSL certificate fix for macOS.

    The 'ssl_fix' command is used to perform an SSL certificate fix for macOS.

    Example Usage:
    ```
    viur tool ssl_fix
    ```

    :return: None
    """
    os.system("chmod +x scripts/macos_certificate_fix.command && ./scripts/macos_certificate_fix.command")
