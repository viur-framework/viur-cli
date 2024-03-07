import json

import click
import os
import shutil
import subprocess

from viur_cli import echo_info, echo_warning
from .conf import config
from . import cli, echo_error, utils
from requests import get
from .package import vi as vi_install
from types import SimpleNamespace


def get_user_info():
    gcloud_auth_process = subprocess.run(['gcloud', 'auth', 'application-default', 'print-access-token'],
                                         capture_output=True,
                                         text=True)

    auth_token = gcloud_auth_process.stdout.strip()  # Extract auth token

    curl_command = f'curl -X GET -H "Authorization: Bearer {auth_token}" "https://www.googleapis.com/oauth2/v1/userinfo?alt=json"'

    curl_process = subprocess.run(curl_command,
                                  capture_output=True, shell = True,
                                  text=True)
    user_info = json.loads(curl_process.stdout)

    return user_info


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("profile", default='default')
@click.argument("additional_args", nargs=-1)
def run(profile, additional_args):
    """
        Start your application locally.
        The 'run' command launches your ViUR application locally specified configuration and optional arguments.
    """
    echo_warning(f"You are using the development Server with your default account: {get_user_info()['email']}")
    conf = config.get_profile(profile)

    utils.system(f'app_server -A={conf["application_name"]} {conf["distribution_folder"]} {" ".join(additional_args)}')

@cli.command()
@click.argument("profile", default="default")
def env(profile):
    """
       Check the local environment for ViUR development.

       The 'env' command provides information about the versions tools and dependencies, such as ViUR-CLI, app_server,
       git, Python, npm, node, and more. It checks the availability of these tools and reports their versions.

    """

    valid_icon = "\U00002714"
    failed_icon = "\U0000274C"

    conf = config.get_profile(profile)
    click.echo(f"Project Info:\n--------------------------------")
    try:
        click.echo(f'format: {config["format"]}')
        for entry in conf["builds"]:
            if entry in conf["builds"]:
                click.echo(f'\n {entry}: {conf["builds"][entry]["version"]} ')

    except Exception as e:
        echo_error("Error while collecting viur info")

        echo_error(str(e))
    click.echo(f"\nCurrent Environment:\n--------------------------------")

    # viur-cli
    if shutil.which("viur"):
        app_server_version = subprocess.check_output(['viur', '--version']).decode("utf-8")
        click.echo(f"{valid_icon} {app_server_version}")
    else:
        click.echo(f"{failed_icon} ViUR-CLI")

    # app_server
    if shutil.which("app_server"):
        app_server_version = subprocess.check_output(['app_server', '-V']).decode("utf-8")
        click.echo(f"{valid_icon} {app_server_version}")
    else:
        click.echo(f"{failed_icon} app_server")

    # git
    if shutil.which("git"):
        git_version = subprocess.check_output(['git', '--version']).decode("utf-8")
        click.echo(f"{valid_icon} {git_version}")
    else:
        click.echo(f"{failed_icon}")

    # python3
    if shutil.which("python3"):
        npm_version = subprocess.check_output(['python3', '-V']).decode("utf-8")
        click.echo(f"{valid_icon} python3 > {npm_version}")
    else:
        click.echo(f"{failed_icon}")

    # python
    if shutil.which("python"):
        npm_version = subprocess.check_output(['python', '-V']).decode("utf-8")
        click.echo(f"{valid_icon} python > {npm_version}")
    else:
        click.echo(f"{failed_icon}")

    # python3
    if shutil.which("pyenv"):
        pyenv_version = subprocess.check_output(['pyenv', '--version']).decode("utf-8")
        click.echo(f"{valid_icon} {pyenv_version}")
    else:
        click.echo(f"{failed_icon}")

    # npm
    if shutil.which("npm"):
        npm_version = subprocess.check_output(['npm', '-v']).decode("utf-8")
        click.echo(f"{valid_icon} npm {npm_version}")
    else:
        click.echo(f"{failed_icon} npm")

    # node
    if shutil.which("node"):
        npm_version = subprocess.check_output(['node', '-v']).decode("utf-8")
        click.echo(f"{valid_icon} node {npm_version}")
    else:
        click.echo(f"{failed_icon} node")

    # pnpm
    if shutil.which("pnpm"):
        npm_version = subprocess.check_output(['pnpm', '-v']).decode("utf-8")
        click.echo(f"{valid_icon} pnpm {npm_version}")
    else:
        click.echo(f"{failed_icon} pnpm (optional)")

    # gcloud
    if shutil.which("gcloud"):
        gcloud_version = subprocess.check_output(['gcloud', '-v']).decode("utf-8").split("\n\n")[0]
        versionList = []
        for line in gcloud_version.split("\n"):
            if not line:
                continue
            if not line.startswith("Google Cloud SDK"):
                line = " - " + line
            versionList.append(line)
        versionString = '\n'.join(versionList)
        click.echo(f"{valid_icon} {versionString}")
    else:
        click.echo(f"{failed_icon} gcloud")

    click.echo(f"Your default gcloud user Info:")
    for k,v in get_user_info().items():
        click.echo(f"{k}: {v}")

@cli.command()
@click.option('--dev', '-d', is_flag=True, default=False)
def check(dev):
    """
    Perform security checks for vulnerabilities.
    The 'check' command helps you identify and address security vulnerabilities in your project's dependencies.
    """

    if do_checks(dev):
        utils.echo_info("\U00002714 No vulnerabilities found.")


def do_checks(dev=True):
    """
    Runs several toolchain and ecosystem security checks for vulnerabilities, and reports these on demand.
    """
    all_checks_passed = True

    def show_output_if_not(args, check_str):
        try:
            result = subprocess.check_output(args, stderr=subprocess.STDOUT, encoding="utf-8")
        except subprocess.CalledProcessError as err:
            result = err.output.strip()

        if check_str not in result:
            print(result)
            return True

        return False

    # Check Pipenv vulnerabilities

    if show_output_if_not("pipenv check --output minimal".split(), "0 vulnerabilities found"):
        all_checks_passed = False

    if dev:
        if show_output_if_not("pipenv check --output minimal --categories develop".split(), "0 vulnerabilities found"):
            all_checks_passed = False

    # Check npm vulnerabilities for all npm builds
    cfg = config.get_profile("default")
    if builds_cfg := cfg.get("builds"):
        if npm_apps := [k for k, v in builds_cfg.items() if builds_cfg[k]["kind"] == "npm"]:
            for name in npm_apps:
                path = os.path.join(cfg["sources_folder"], builds_cfg[name]["source"])

                if dev:
                    args = ("npm", "audit", "--prefix", path)
                else:
                    args = ("npm", "audit", "--omit", "dev", "--prefix", path)

                if show_output_if_not(args, "found 0 vulnerabilities"):
                    all_checks_passed = False

    return all_checks_passed
