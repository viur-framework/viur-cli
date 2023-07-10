import click
import os

from . import cli


@cli.group()
def tool():
    """run different viur related scripts"""


@tool.command(name="2to3")
@click.argument("path")
@click.option('--dryrun', '-d', is_flag=True, default=False)
@click.option('--daredevil', '-x', is_flag=True, default=False)
def two_to_three(path, *args, **kwargs):
    """viur porting script"""
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
    """flare build script"""
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
    """run the get_pyodide command"""
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
    """ssl fix for macos"""
    os.system("chmod +x scripts/macos_certificate_fix.command && ./scripts/macos_certificate_fix.command")
