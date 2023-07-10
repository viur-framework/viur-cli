"""
Everything related to maintaining the project.json configuration file for a viur project.
"""

import click
import os
import json
from .utils import *
from pathlib import Path

DEFAULT_PYODIDE_VERSION = "0.19.1"

projectConfig = None
projectConfigFilePath = "project.json"


# functions
@click.pass_context
def create_new_config(ctx, path=None):
    """create new config with project.json default template"""

    if path and os.path.exists(os.path.join(os.path.dirname(path), "deploy")):
        deployFolder = "./deploy"
    else:
        deployFolder = click.prompt('distribution folder', default="./deploy")

    if path and os.path.exists(os.path.join(os.path.dirname(path), "sources")):
        sourcesFolder = "./sources"
    else:
        sourcesFolder = click.prompt('distribution folder', default="./sources")



    _projectconf = {
        "default": {
            "format":"1.0.0",
            "distribution_folder": deployFolder,
            "sources_folder": sourcesFolder,
            "builds": {},
            "vi": "submodule",
            "core": "submodule",
            "pyodide": click.prompt('pyodide', default=DEFAULT_PYODIDE_VERSION)
        },

        "develop": {
            "application_name": click.prompt('application name'),
            "version": click.prompt('develop version name')
        }
    }

    if click.confirm("Do you want to use a prebuild Vi? (default)",
                     default=True,
                     show_default=True):
        write_config(_projectconf, path)
        from .vi import vi
        ctx.invoke(vi)
    else:
        if os.path.exists("./sources/vi"):
            echo_info("Found vi application. Added to projet.json.")
            _projectconf["default"]["builds"].update({
                'vi': {
                    "kind": "flare",
                    "source": './sources/vi/vi',
                    "target": './deploy/vi'
                }
            })
        elif click.confirm("Do you want to add vi as submodule(default)",
                           default=True,
                           show_default=True):
            os.system(
                f'git submodule add https://github.com/viur-framework/viur-vi sources/vi && git submodule update --init --recursive')
            _projectconf["default"]["builds"].update({
                'vi': {
                    "kind": "flare",
                    "source": './sources/vi/vi',
                    "target": './deploy/vi'
                }
            })
            _projectconf["default"]["vi"] = f'submodule'

    if click.confirm("Do you want to add additional flare application?"):
        _projectconf = add_to_flare_config(_projectconf)

    write_config(_projectconf, path)


def load_config(path=None):
    """load project.json and write to global projectConfig"""
    global projectConfig

    if not path:
        path = projectConfigFilePath

        # Search in any parent folder for a project.json,
        # change working directory because subsequent commands
        # require for project root folder.
        changed = False
        while not os.path.exists(path):
            os.chdir("..")
            changed = True

            if os.getcwd() == "/":
                echo_fatal(f"{path} not found - please check if you are in the right folder.")

        if changed:
            echo_info(f"Project root is {os.getcwd()}")

    try:
        f = open(path, "r")
        projectConfig = json.loads(f.read())
    except FileNotFoundError:
        echo_fatal(f"Can't open {path} for reading")

    except json.decoder.JSONDecodeError as e:
        echo_fatal(f"The configuration in {path} contains invalid JSON: {str(e)}. Please verify right syntax.")

    update_config(path)
    return projectConfig


def write_config(conf, path=None):
    """write current projectConfig dict to project.json"""
    global projectConfig

    projectConfig = conf

    if not path:
        path = projectConfigFilePath

    f = open(path, "w")
    f.write(json.dumps(conf, indent=4, sort_keys=True))
    f.close()


def get_config():
    global projectConfig
    return projectConfig


def add_to_config():
    """add a new config to project.json"""
    global projectConfig
    if not projectConfig:
        return

    projectConfig.update({click.prompt('name'): {
        "application_name": click.prompt('application name'),
        "version": click.prompt('develop version name')
    }})

    write_config(projectConfig)


def remove_from_config():
    """remove a config from project.json"""
    global projectConfig
    configname = click.prompt('name')
    try:
        del projectConfig[configname]
        write_config(projectConfig)
    except:
        raise click.ClickException(click.style(f"{configname} not found", fg="red"))


def add_to_flare_config(projectconf):
    """add a new flare app to project.json"""
    if "default" not in projectconf:
        raise click.ClickException(click.style("default entry is missing", fg="red"))

    if not "builds" in projectconf["default"]:
        projectconf["default"].update({"builds": {}})

    projectconf["default"]["builds"].update({
        click.prompt('name'): {
            "kind": "flare",
            "source": click.prompt('source'),
            "target": click.prompt('target')
        }
    })

    return projectconf


def remove_from_flare_config(flareAppName):
    """remove a flare app from project.json"""
    global projectConfig
    try:
        del projectConfig["default"]["builds"][flareAppName]
        write_config(projectConfig)
    except:
        raise click.ClickException(click.style(f"{flareAppName} not found", fg="red"))


def fetch_core_version():
    try:
        result = os.popen('pip list --format=json').read()
        coreVersion = [x for x in json.loads(result) if x["name"] == "viur-core"][0]["version"]

        projectConfig["default"]["core"] = coreVersion
        write_config(projectConfig)
    except:
        if projectConfig and projectConfig["default"]:
            projectConfig["default"]["core"] = "submodule"
            write_config(projectConfig)

def add_npm_apps():
    global projectConfig
    if "default" not in projectConfig:
        raise click.ClickException(click.style("default entry is missing", fg="red"))

    sourceFolder = projectConfig["default"]["sources_folder"]

    for path in Path(sourceFolder).rglob('package.json'):
        if "/node_modules/" not in str(path):
            sourcepath = str(path).replace(sourceFolder[2:],"").replace("package.json","")

            if "/vi/vi/" in sourcepath or "/examples/" in sourcepath or "/example/" in sourcepath:
                continue

            if sourcepath == "/vi/vi-base/":
                if click.confirm(f"Do you want to add the vue vi to your apps?"):
                    projectConfig["default"]["builds"].update({
                        "vvi": {
                            "kind": "npm",
                            "source": sourcepath[:-1],
                            "command": "build"
                        }
                    })

            elif click.confirm(f"Do you want to add {sourcepath} to your apps?"):
                if not "builds" in projectConfig["default"]:
                    projectConfig["default"].update({"builds": {}})

                pathparts = sourcepath.strip("/").split("/")
                if len(pathparts) == 1:
                    defaultname = sourcepath.strip("/").split("/")[0].replace("viur-", "")
                elif len(pathparts) > 1:
                    defaultname = sourcepath.strip("/").split("/")[0].replace("viur-", "")+"_"+sourcepath.strip("/").split("/")[-1].replace("viur-", "")
                else:
                    defaultname = None


                projectConfig["default"]["builds"].update({
                    click.prompt('name', default=defaultname): {
                        "kind": "npm",
                        "source": sourcepath[:-1],
                        "command": click.prompt('command', default="build")
                    }
                })
    return projectConfig


def update_config(path=None):
    assert projectConfig, "load_config() must be called first!"

    assert projectConfig["default"]["format"] in ["1.0.0", "1.0.1", "1.1.0", "1.1.1"], "Invalid formatversion, you have to fix it manually"

    if "format" not in projectConfig["default"]:
        projectConfig["default"]["format"] = "1.0.1"

    if "pyodide" not in projectConfig["default"]:
        projectConfig["default"]["pyodide"] = DEFAULT_PYODIDE_VERSION

    ##################### Version 1.0.1

    if projectConfig["default"]["pyodide"].startswith("v"):
        projectConfig["default"]["pyodide"] = projectConfig["default"]["pyodide"][1:] #remove v prefix

    if projectConfig["default"]["vi"].startswith("v"):
        projectConfig["default"]["vi"] = projectConfig["default"]["vi"][1:]  # remove v prefix

    if projectConfig["default"]["format"] == "1.0.0":
        projectConfig["default"]["format"] = "1.0.1"

    ##################### Version 1.1.0

    if "flare" in projectConfig["default"]:
        builds = projectConfig["default"]["flare"].copy()
        for k,v in builds.items():
            builds[k]["kind"] = "flare"

        projectConfig["default"]["builds"] = builds
        del projectConfig["default"]["flare"]

    if projectConfig["default"]["format"] == "1.0.1":
        projectConfig["default"]["format"] = "1.1.0"
        echo_info("viur-cli tries to find npm applications")
        add_npm_apps()

    ##################### Version 1.1.1

    if projectConfig["default"]["format"] == "1.1.0":
        projectConfig["default"]["format"] = "1.1.1"
        builds = projectConfig["default"].get("builds", {}).copy()
        for k, v in builds.items():
            if builds[k]["kind"] == "script":
                builds[k]["kind"] = "exec"
        projectConfig["default"]["builds"] = builds

    # conf updates must increase format version
    write_config(projectConfig, path)




