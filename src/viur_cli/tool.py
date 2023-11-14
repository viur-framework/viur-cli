import click
import os

from . import cli


@cli.group()
def tool():
    """
    Run different ViUR-related scripts.

    The 'tool' group allows you to execute various ViUR-related scripts that help with tasks such as project porting,
    Flare builds, Pyodide installation, and SSL certificate fixes.

    Usage:
    ```
    viur tool <command> [options]
    ```

    Available Commands:
    - '2to3': ViUR porting script.
    - 'flare': Flare build script.
    - 'pyodide': Run the get_pyodide command.
    - 'ssl_fix': SSL certificate fix for macOS.

    Use 'viur tool <command> -h' for command-specific help.

    Example Usage:
    ```
    viur tool 2to3 /path/to/project
    ```

    :return: None
    """


@tool.command(name="2to3")
@click.argument("path")
@click.option('--dryrun', '-d', is_flag=True, default=False)
@click.option('--daredevil', '-x', is_flag=True, default=False)
def two_to_three(path, *args, **kwargs):
    """
    ViUR2 to ViUR3 porting script.

    The '2to3' command allows you to port an existing ViUR2 project to ViUR3. This script is used for
    migrating projects from Python 2 to Python 3.

    :param path: str
        The path to the project to be ported.
    :param dryrun: bool, optional
        Perform a dry run to test the porting process (default: False).
    :param daredevil: bool, optional
        Use the daredevil mode for porting (default: False).

    Example Usage:
    ```
    viur tool 2to3 /path/to/project
    ```

    :return: None
    """
    command = f"viur-2to3 {path}"
    for option, value in kwargs.items():
        if value:
            command += f" --{option}"

    os.system(command)


@tool.command()
@click.option('--source', '-s')
@click.option('--target', '-t')
@click.option('--name', '-n')
@click.option('--minify', '-m', is_flag=True, default=False)
@click.option('--compile', '-c', is_flag=True, default=False)
@click.option('--zip', '-z', is_flag=True, default=False)
@click.option('--watch', '-w', is_flag=True, default=False)
def flare(*args, **kwargs):
    """
    Flare build script.

    The 'flare' command allows you to run the Flare build script, which compiles ViUR Flare applications.

    :param source: str, optional
        The source directory for Flare applications.
    :param target: str, optional
        The target directory for compiled Flare applications.
    :param name: str, optional
        The name of the Flare application.
    :param minify: bool, optional
        Minify the compiled JavaScript and CSS (default: False).
    :param compile: bool, optional
        Compile Flare applications (default: False).
    :param zip: bool, optional
        Create a ZIP archive of the compiled Flare application (default: False).
    :param watch: bool, optional
        Watch for changes and recompile (default: False).

    Example Usage:
    ```
    viur tool flare --source /source/path --target /target/path --name myapp --minify --compile
    ```

    :return: None
    """
    command = "flare"
    for option, value in kwargs.items():
        if value and isinstance(value, bool):
            command += f" --{option}"
        elif value:
            command += f" --{option} {value}"
    os.system(command)


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
