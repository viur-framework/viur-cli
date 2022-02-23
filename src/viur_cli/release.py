import click, os, shutil
from . import cli, echo_error, get_config,utils


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("name", default='develop')
@click.argument("additional_args", nargs=-1)
def release(name, additional_args):
    """create a release build"""

    utils.echo_info("building started...")
    projectConfig = get_config()

    if not os.popen("pyenv versions").read():
        echo_error(f"pyenv not found!")
        return

    if name not in projectConfig:
        echo_error(f"{name} is not a valid config name.")
        return

    conf = projectConfig["default"].copy()
    conf.update(projectConfig[name])

    #get pyodide 0.19. Enforce pyodide
    if not conf.get("pyodide"):
        pyodide_version = "v0.19.0"
    else:
        pyodide_version = conf.get("pyodide")

    os.system(f'get-pyodide -t {conf["distribution_folder"]}/pyodide -v {pyodide_version}')

    #build all flare apps
    if conf.get("flare"):
        if "debug" in additional_args:
            flare_build_type = "debug"
            flare_build_env = ""
        else:
            flare_build_type = "release"
            flare_build_env = "pyenv exec"

            #enforce python 3.9.5
            if "3.9.5" not in os.popen("pyenv versions").read():
                os.system(f'pyenv install 3.9.5')
            os.system("pyenv local 3.9.5")

        for name,flare in conf["flare"].items():
            os.system(f'{flare_build_env} viur flare {flare_build_type} {name}')

        if flare_build_type == "release":
            os.system("pyenv local system")

    #build all other apps and assets
    os.system('viur npm')
    utils.echo_info("building finished!")



