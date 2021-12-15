import click, os, shutil, json
from . import cli, echo_error, get_config


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", default="build", type=click.Choice(['init', 'build']))
@click.argument("additional_args", nargs=-1)
def assets(action, additional_args):
    """build gulp assets"""

    additional_args = list(additional_args)

    if action == "init":
        assets_init(additional_args)
    elif action == "build":
        assets_build(additional_args)


def assets_init(additional_args):
    sources_folder = get_config()["default"]["sources_folder"]
    try:
        f = open(os.path.join(sources_folder, "package.json"), "r")
        packageJson = json.loads(f.read())

        if "gulp" in packageJson["dependencies"] or "gulp" in packageJson["devDependencies"]:
            os.system(f'cd {sources_folder} && rm -rf node_modules && npm install --force')
            return True
        else:
            raise Exception("no gulp found")
    except:
        echo_error("no package.json or gulp found. Please check your sources folder")

    return False


def assets_build(additional_args):
    sources_folder = get_config()["default"]["sources_folder"]

    if not os.path.exists(os.path.join(sources_folder, "node_modules")):
        # init sources folder
        init_ok = assets_init(additional_args)
    else:
        try:
            # test gulp existance
            f = open(os.path.join(sources_folder, "package.json"), "r")
            packageJson = json.loads(f.read())

            if "gulp" in packageJson["dependencies"] or "gulp" in packageJson["devDependencies"]:
                init_ok = True
            else:
                init_ok = False
        except:
            init_ok = False

    if not init_ok:
        # only run if initialized and gulp exists
        echo_error(f"assets cant be build, please check your sources folder")
        return 0

    os.system(f'cd {sources_folder} && npx gulp')
