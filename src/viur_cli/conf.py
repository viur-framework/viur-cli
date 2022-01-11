import click
import os
import json
from .utils import *
from typing import Callable, Union, Dict

projectConfig = None
projectConfigFilePath = "./project.json"


# functions
#@click.pass_context
def create_new_config(path=None, deploy_cb: Callable[[], str] = None, 
                      sources_cb: Callable[[], str] = None, 
                      app_name: str = "",
                      version_name: str = "",
                      use_prebuild_vi: bool = True,
                      vi_as_submodule : Callable[[], bool] = None,
                      additional_flare_app: Callable[[], bool] = None) -> None:
    """create new config with project.json default template"""

    if path and os.path.exists(os.path.join(os.path.dirname(path), "deploy")):
        deployFolder = "./deploy"
    else:
        deployFolder = deploy_cb()

    if path and os.path.exists(os.path.join(os.path.dirname(path), "sources")):
        sourcesFolder = "./sources"
    else:
        sourcesFolder = sources_cb()

    _projectconf = {
        "default": {
            "distribution_folder": deployFolder,
            "sources_folder": sourcesFolder,
            "flare": {},
            "vi": "submodule",
            "core": "submodule"
        },

        "develop": {
            "application_name": app_name,
            "version": version_name,
        }
    }

    if use_prebuild_vi:
        write_config(_projectconf, path)
        from .vi import _vi
        #ctx.invoke(vi)
        _vi()
    else:
        if os.path.exists("./sources/vi"):
            echo_info("Found vi application. Added to project.json.")
            _projectconf["default"]["flare"].update({
                'vi': {
                    "source": './sources/vi/vi',
                    "target": './deploy/vi'
                }
            })
        elif vi_as_submodule():
            os.system(
                f'git submodule add https://github.com/viur-framework/viur-vi sources/vi && git submodule update --init --recursive')
            _projectconf["default"]["flare"].update({
                'vi': {
                    "source": './sources/vi/vi',
                    "target": './deploy/vi'
                }
            })
            _projectconf["default"]["vi"] = f'submodule'

    if additional_flare_app():
        _projectconf = add_to_flare_config(_projectconf)

    write_config(_projectconf, path)

def create_new_config_extended(path=None):
    create_new_config(path=path, 
        deploy_cb=lambda: click.prompt('distribution folder', default="./deploy"),
        sources_cb=lambda: click.prompt('distribution folder', default="./sources"),
        app_name = click.prompt('application name'),
        version_name = click.prompt('develop version name'),
        use_prebuild_vi = click.confirm("Do you want to use a prebuild Vi? (default)",default=True,show_default=True),
        vi_as_submodule = lambda: click.confirm("Do you want to add vi as submodule(default)", default=True, show_default=True),
        additional_flare_app = lambda: click.confirm("Do you want to add additional flare application?")
    )

def load_config(path=None):
    """load project.json and write to global projetConfig"""
    global projectConfig

    try:
        if not path:
            path = projectConfigFilePath

        f = open(path, "r")
        projectConfig = json.loads(f.read())
    except:
        echo_error("no project.json found")

    return projectConfig


def write_config(conf, path : Union[None, str] = None) -> None:
    """write current projectConfig dict to project.json"""
    global projectConfig

    projectConfig = conf

    if not path:
        path = projectConfigFilePath

    f = open(path, "w")
    f.write(json.dumps(conf, indent=4, sort_keys=True))
    f.close()


def get_config() -> Union[Dict[str, str], None]:
    global projectConfig
    return projectConfig


def add_to_config(name: str, application_name: str, version: str) -> None:
    """add a new config to project.json"""
    global projectConfig
    if not projectConfig:
        return

    projectConfig.update({name: {
        "application_name": application_name,
        "version": version
    }})

    write_config(projectConfig)

def remove_from_config(config_name: str);
    global projectConfig
    try:
        del projectConfig[config_name]
        write_config(projectConfig)
    except:
        raise click.ClickException(click.style(f"{config_name} not found", fg="red"))

def add_to_flare_config(projectconf: Dict[str, str], name: str, source: str, target: str) -> Dict[str, str]:
    if "default" not in projectconf:
        raise ValueError("default entry is missing")

    if not "flare" in projectconf["default"]:
        projectconf["default"].update({"flare": {}})

    projectconf["default"]["flare"].update({
        name: {
            "source": source,
            "target": target
        }
    })

    return projectconf

def remove_from_flare_config(flare_app_name: str):
    """remove a flare app from project.json"""
    global projectConfig
    try:
        del projectConfig["default"]["flare"][flare_app_name]
        write_config(projectConfig)
    except:
        raise click.ClickException(click.style(f"{flare_app_name} not found", fg="red"))


def fetch_core_version() -> None:
    try:
        result = os.popen('pip list --format=json').read()
        coreVersion = [x for x in json.loads(result) if x["name"] == "viur-core"][0]["version"]

        projectConfig["default"]["core"] = coreVersion
        write_config(projectConfig)
    except:
        if projectConfig and projectConfig["default"]:
            projectConfig["default"]["core"] = "submodule"
            write_config(projectConfig)
