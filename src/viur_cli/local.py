import click, os, shutil, subprocess
from . import cli, echo_error, get_config, utils
from .install import vi as vi_install


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("name", default='develop')
@click.argument("additional_args", nargs=-1)
def run(name, additional_args):
    """start your application locally"""
    projectConfig = get_config()

    if name not in projectConfig:
        echo_error(f"{name} is not a valid config name.")
        return

    conf = projectConfig["default"].copy()
    conf.update(projectConfig[name])

    utils.system(f'app_server -A={conf["application_name"]} {conf["distribution_folder"]} {" ".join(additional_args)}')


@cli.command()
def env():
    """check local Environment"""
    valid_icon = "\U00002714"
    failed_icon = "\U0000274C"

    projectConfig = get_config()

    click.echo(f"Project Info:\n--------------------------------")
    try:
        click.echo(f'Vi: {projectConfig["default"]["vi"]}')
        click.echo(f'Core: {projectConfig["default"]["core"]}')
        click.echo(f'Pyodide: {projectConfig["default"]["pyodide"]}')
        click.echo(f'format: {projectConfig["default"]["format"]}')
    except:
        echo_error("Error while collecting viur info")
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
@click.argument("action", type=click.Choice(['npm', 'all']))
@click.option('--autofix', '-a', is_flag=True, default=False)
def check(dev, action, autofix):
    """do security checks"""
    if dev:
        do_checks()
        utils.echo_info("\U00002714 No vulnerabilities found.")

    if action == "npm":
        npm_audit_with_prompt()
        #checknpm(autofix)

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
    projectConfig = get_config()
    cfg = projectConfig["default"].copy()
    print(cfg.get("builds"))
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

    ############################### Change to your actual folder path

    return all_checks_passed

# viur check npm --autofix

def checknpm(autofix):
    sources_folder = './sources'
    try:
        result = subprocess.check_output(
            ['npm', 'audit'], stderr=subprocess.STDOUT, cwd=sources_folder, encoding='utf-8')
        print(result)
        if "found 0 vulnerabilities" not in result and autofix:

            click.echo(result)
            confirm = click.prompt('Vulnerabilities found. Run "npm audit fix" automatically? (Y/n)',
                                   default='Y').strip().lower()
            if confirm == 'y':
                subprocess.run(['npm', 'audit', 'fix'], cwd=sources_folder)
            else:
                click.echo(
                    'Automatic fix not confirmed. To fix vulnerabilities, '
                    'run "npm audit fix" in the ./sources folder.')

        click.echo('No vulnerabilities found.')
        click.echo('To fix vulnerabilities, run "npm audit fix" in the ./sources folder.')

    except:
        print("An error occured")

def npm_audit_with_prompt():
    sources_folder = './sources'

    try:
        # Run "npm audit" command and capture the output
        result = subprocess.run(
            ['npm', 'audit'],
            stderr=subprocess.STDOUT,
            cwd=sources_folder,
            encoding='utf-8',
            stdout=subprocess.PIPE
        )

        # Print the "npm audit" output

        print(result.stdout)
        print("THIS WAS RESULT.STDOUT")

        if "found 0 vulnerabilities" not in result.stdout:
            confirm = input('Vulnerabilities found. Run "npm audit fix" automatically? (Y/n): ').strip().lower()
            if confirm == 'y' or confirm == 'Y':
                # Run "npm audit fix" if the user confirms
                fix_result = subprocess.run(
                    ['npm', 'audit', 'fix'], cwd=sources_folder, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(fix_result.stdout)
            else:
                print('Automatic fix not confirmed. To fix vulnerabilities, run "npm audit fix" in the ./sources folder.')

        else:
            print('No vulnerabilities found.')

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
