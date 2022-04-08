import click, os, shutil
from . import cli, echo_error, utils, conf


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("name", default='develop')
@click.argument("additional_args", nargs=-1)
def release(name, additional_args):
    """create a release build"""

    utils.echo_info("building started...")
    projectConfig = conf.get_config()

    if not os.popen("pyenv versions").read():
        echo_error(f"pyenv not found!")
        return

    if name not in projectConfig:
        echo_error(f"{name} is not a valid config name.")
        return

    cfg = projectConfig["default"].copy()
    cfg.update(projectConfig[name])

    #build all flare apps
    if flare_cfg := cfg.get("flare"):
        # Ensure for local pyodide.
        pyodide_version = cfg.get("pyodide", conf.DEFAULT_PYODIDE_VERSION)
        utils.echo_info(f"- Ensuring Pyodide {pyodide_version} local install")

        os.system(f'get-pyodide -t {cfg["distribution_folder"]}/pyodide -v {pyodide_version}')

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

        for name in flare_cfg.keys():
            utils.echo_info(f"- Building {flare_build_type} {name}")
            os.system(f'{flare_build_env} viur flare {flare_build_type} {name}')

        if flare_build_type == "release":
            os.system("pyenv local system")

    #build all other apps and assets
    os.system('viur npm')
    utils.echo_info("building finished!")



