"""
Everything related to maintaining the project.json configuration file for a viur project.
"""

import json
from .utils import *

DEFAULT_PYODIDE_VERSION = "0.19.1"

pectConfig = None
projectConfigFilePath = "project.json"


def load_config(path=None):
    """
        Load project.json and write to the global projectConfig.

        This function is responsible for loading the project.json configuration file and populating the global projectConfig
        variable. It handles error checks, such as missing or invalid JSON configuration files, and updates the project
        configuration.

        :param path: str, optional
            The path to the project.json file. If not provided, the default projectConfigFilePath is used.

        :return: dict
            The project configuration loaded from the project.json file.
        """
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
    """
    Write the current projectConfig dictionary to project.json.

    This function is used to write the current project configuration, provided as a dictionary, to the project.json file.

    :param conf: dict
        The project configuration to be written to the project.json file.

    :param path: str, optional
        The path to the project.json file. If not provided, the default projectConfigFilePath is used.

    :return: None
    """
    global projectConfig

    projectConfig = conf

    if not path:
        path = projectConfigFilePath

    f = open(path, "w")
    f.write(json.dumps(conf, indent=4, sort_keys=True))
    f.close()


def get_config():
    """
        Get the current project configuration.

        This function returns the current project configuration stored in the global projectConfig variable.

        :return: dict
            The project configuration.
    """
    global projectConfig
    return projectConfig


def add_to_config():
    """
        Add a new configuration to project.json.

        This function allows the addition of a new configuration to the project.json file. It prompts for the configuration name,
        application name, and version.

        :return: None
    """
    global projectConfig
    if not projectConfig:
        return

    projectConfig.update({click.prompt('name'): {
        "application_name": click.prompt('application name'),
        "version": click.prompt('develop version name')
    }})

    write_config(projectConfig)


def remove_from_config():
    """
    Remove a configuration from project.json.

    This function allows the removal of an existing configuration from the project.json file. It prompts for the
    configuration name to remove.

    :return: None
    """
    global projectConfig
    configname = click.prompt('name')
    try:
        del projectConfig[configname]
        write_config(projectConfig)
    except:
        raise click.ClickException(click.style(f"{configname} not found", fg="red"))


def add_to_flare_config(projectconf):
    """
    Add a new Flare app configuration to project.json.

    This function is used to add a new Flare app configuration to the project.json file. It prompts for the app name,
    source, and target.

    :param projectconf: dict
        The project configuration where the Flare app configuration will be added.

    :return: dict
        The updated project configuration with the new Flare app configuration.
    """
    if "default" not in projectconf:
        raise click.ClickException(click.style("default entry is missing", fg="red"))

    if "builds" not in projectconf["default"]:
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
    """
    Remove a Flare app configuration from project.json.

    This function allows the removal of an existing Flare app configuration from the project.json file. It prompts for the
    Flare app name to remove.

    :param flareAppName: str
        The name of the Flare app to remove from the project configuration.

    :return: None
    """
    global projectConfig
    try:
        del projectConfig["default"]["builds"][flareAppName]
        write_config(projectConfig)
    except:
        raise click.ClickException(click.style(f"{flareAppName} not found", fg="red"))


def fetch_core_version():
    """
    Fetch the version of the 'viur-core' package.

    This function is responsible for fetching the version of the 'viur-core' package using 'pip list' and updating
    the project configuration accordingly.

    :return: None
    """
    try:
        result = os.popen('pip list --format=json').read()
        coreVersion = [x for x in json.loads(result) if x["name"] == "viur-core"][0]["version"]

        projectConfig["default"]["core"] = coreVersion
        write_config(projectConfig)
    except:
        if projectConfig and projectConfig["default"]:
            projectConfig["default"]["core"] = "submodule"
            write_config(projectConfig)


def update_config(path=None):
    """
    Update the project configuration.

    This function performs updates and migrations on the project configuration as needed. It includes version checks
    and format updates. Ensure that 'load_config()' is called before invoking this function.

    :param path: str, optional
        The path to the project.json file. If not provided, the root directory of the project. is used.

    :return: None
    """
    assert projectConfig, "load_config() must be called first!"

    assert projectConfig["default"]["format"] in ["1.0.0", "1.0.1", "1.1.0", "1.1.1"], "Invalid formatversion, you have to fix it manually"

    if "format" not in projectConfig["default"]:
        projectConfig["default"]["format"] = "1.0.1"

    ##################### Version 1.0.1

    if (pyodide_version := projectConfig["default"].get("pyodide")) and pyodide_version.startswith("v"):
        projectConfig["default"]["pyodide"] = pyodide_version[1:] #remove v prefix

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




