import json
import click
import os
import shutil
import subprocess
from pprint import pprint
from .conf import config
from . import cli, echo_error, utils
from .install import vi as vi_install
from types import SimpleNamespace


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("profile", default='default')
@click.argument("additional_args", nargs=-1)
def run(profile, additional_args):
    """
        Start your application locally.

        The 'run' command allows you to start your ViUR application locally. You can specify the configuration to use
        and provide additional arguments to the 'app_server' command.

        :param name: str, default: 'develop'
            The name of the configuration to use. The 'develop' configuration is the default.

        :param additional_args: List[str]
            Additional arguments to pass to the 'app_server' command when running the application.

        Example Usage:
        ```shell
        viur run develop --port 8080
        viur run production
        ```

        The 'run' command launches your ViUR application locally specified configuration and optional arguments.

        :return: None
    """

    conf = config.get_profile(profile)

    utils.system(f'app_server -A={conf["application_name"]} {conf["distribution_folder"]} {" ".join(additional_args)}')

@cli.command()
@click.argument("profile", default="default")
def env(profile):
    """
       Check the local environment for ViUR development.

       The 'env' command checks the local environment for ViUR development and reports the status of various tools
       and dependencies. It helps you ensure that your development environment is correctly set up.

       Usage:
       ```shell
       viur env
       ```

       The 'env' command provides information about the versions tools and dependencies, such as ViUR-CLI, app_server,
       git, Python, npm, node, and more. It checks the availability of these tools and reports their versions.

       :return: None
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


@cli.command()
@click.option('--dev', '-d', is_flag=True, default=False)
@click.option('--autofix', '-a', is_flag=True, default=False)
@click.argument("action", type=click.Choice(['npm', 'all']))
def check(dev, action, autofix):
    """
    Perform security checks for vulnerabilities.

    The 'check' command performs security checks for vulnerabilities within your project.
    It checks for vulnerabilities in the Pipenv and npm dependencies of your project.
    You can choose to include development dependencies by using the '--dev' option.

    Args:
        dev (bool): Perform checks on development dependencies if set to 'True'.
        autofix (bool): Automatically fix npm vulnerabilities if set to 'True'.
        action (str): Specify the action to perform ('npm' or 'all').

    The 'check' command helps you identify and address security vulnerabilities in your project's dependencies.

    Usage:
    ```shell
       viur check --dev npm --autofix
    ```
    """
    if do_checks(dev):
        utils.echo_info("\U00002714 No vulnerabilities found.")

    if action == "npm":
        checknpm(autofix)

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
        if show_output_if_not("pipenv check --output minimal --categories develop".split(),
                              "0 vulnerabilities found"):
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


def checknpm(autofix):
    """
    Check for npm vulnerabilities in the project and optionally fix them.

    This function runs the "npm audit" command to check for vulnerabilities in the project's dependencies. If any
    vulnerabilities are found, the function prompts the user to view the details and optionally run "npm audit fix
    --force" to automatically fix the vulnerabilities.

    Args:
        autofix (bool): A boolean indicating whether to automatically fix vulnerabilities.

    Raises:
        subprocess.CalledProcessError: If an error occurs while running the "npm audit" or "npm audit fix" commands.
    """
    project_config = get_config()
    sources_folder = project_config["default"]["sources_folder"]

    try:
        # Run "npm audit" command and capture the output
        result = subprocess.run(
            ['npm', 'audit', '--json'],
            capture_output=True,
            cwd=sources_folder,
            encoding='utf-8'
        )

        audit = json.loads(result.stdout)
        vulnerabilities = audit["metadata"]["vulnerabilities"]

        if vulnerabilities["total"] >= 0:

            if not autofix:
                print(
                    f'Npm found {vulnerabilities["total"]} Vulnerabilities \n'
                    f'info: {vulnerabilities["info"]}\n'
                    f'low: {vulnerabilities["low"]}\n'
                    f'moderate: {vulnerabilities["moderate"]}\n'
                    f'high: {vulnerabilities["high"]}\n'
                    f'critical: {vulnerabilities["critical"]}\n'
                    f'total: {vulnerabilities["total"]}\n'
                )
                show_vulnerabilities = input('Do you want a list of the found Vulnerabilities? (y/N)').strip().lower()

                if show_vulnerabilities == 'y':
                    pprint(audit["vulnerabilities"])

                confirm = input('Do you want to run "npm audit fix --force" automatically? (Y/n):').strip().lower()

            if autofix or confirm == 'y' or confirm == '':

                try:
                    fix = subprocess.run(
                        ["npm", "audit", "fix", "--force",  "--json"],
                        capture_output=True,
                        cwd=sources_folder,
                        encoding="utf-8",
                    )

                    fix_output = json.loads(fix.stdout)

                    echo_info(
                        f'npm added {fix_output["added"]} packages,\n'
                        f'audited {fix_output["audited"]} packages,\n'
                        f'changed {fix_output["changed"]} packages\n'
                        f'and removed {fix_output["removed"]} packages\n'
                    )

                    show_all_fix = input('Do you want the whole report of the npm fixes?(y/N)').lower().strip()
                    if show_all_fix == 'y':
                        pprint(fix_output)

                except Exception as e:
                    echo_error(f'{e}')
            else:
                echo_info(
                    'Automatic fix not confirmed. To fix vulnerabilities, '
                    'run "npm audit fix --force" in the ./sources folder.'
                )
        else:
            echo_positive('No vulnerabilities found.')

    except Exception as e:
        echo_error(f'An unexpected error occurred: {e}')
