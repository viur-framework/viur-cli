import json
import click
from .utils import *


PROJECT_CONFIG_FILE = "project.json"
PROJECT_CONFIG_VERSION = "2.0.0"


class ProjectConfig(dict):

    def __init__(self):
        super().__init__()
        self["default"] = {}
        self["format"] = PROJECT_CONFIG_VERSION
        self.load()

    def load(self):
        """
            Load project.json and write to the global projectConfig.

            This function is responsible for loading the project.json configuration file and populating the global
            projectConfig variable.
            It handles error checks, such as missing or invalid JSON configuration files, and updates the project
            configuration.

            :param path: str, optional
                The path to the project.json file. If not provided, the default projectConfigFilePath is used.

            :return: dict
                The project configuration loaded from the project.json file.
        """


        # Search in any parent folder for a project.json,
        # change working directory because subsequent commands
        # require for project root folder.
        changed = False
        while not os.path.exists(PROJECT_CONFIG_FILE):
            os.chdir("..")
            changed = True

            if os.getcwd() == "/":
                echo_fatal(f"{PROJECT_CONFIG_FILE} not found - please check if you are in the right folder.")

        if changed:
            echo_info(f"Project root is {os.getcwd()}")

        try:
            f = open(PROJECT_CONFIG_FILE, "r")
            self.update(json.loads(f.read()))

        except FileNotFoundError:
            echo_fatal(f"Can't open {PROJECT_CONFIG_FILE} for reading")

        except json.decoder.JSONDecodeError as e:
            echo_fatal(f"The configuration in {PROJECT_CONFIG_FILE} contains invalid JSON: {str(e)}. Please verify right syntax.")

        self.migrate()

    def save(self):
        """
        Write the current projectConfig dictionary to project.json.
        """
        with open(PROJECT_CONFIG_FILE, "w") as f:
            json.dump(self, f, indent=4, sort_keys=True))
            f.write('\n')

    def get_profile(self, profile):
        if profile == "format":
            echo_fatal("Your profile can not be named 'Format' ")
        return self["default"].copy() | self[profile]

    def delete(self):
        configname = click.prompt('name')
        try:
            del self[configname]
            self.save()
        except:
            raise click.ClickException(click.style(f"{configname} not found", fg="red"))

    def migrate(self):

        assert self["format"] in ["1.0.0", "1.0.1", "1.1.0", "1.1.1", "1.2.0", PROJECT_CONFIG_VERSION], \
            "Invalid formatversion, you have to fix it manually"

        # Version 1.0.1
        if (pyodide_version := self["default"].get("pyodide")) and pyodide_version.startswith("v"):
            self["default"]["pyodide"] = pyodide_version[1:]  # remove v prefix

        if self["format"] == "1.0.0":
            self["format"] = "1.0.1"

        # Version 1.1.1
        if self["format"] == "1.1.0":
            self["format"] = "1.1.1"
            builds = self["default"].get("builds", {}).copy()
            for k, v in builds.items():
                if builds[k]["kind"] == "script":
                    builds[k]["kind"] = "exec"
            self["default"]["builds"] = builds

        # Version 1.2.0
        """
            Convert versions in the configuration to builds.

            This method iterates through the provided version list and updates the project configuration
            by converting versions to builds.

            :param version_list: list
                List of versions to convert to builds.
            :return: None
        """
        # Check if Builds is in the project.json
        if "builds" not in self["default"].keys():
            self["default"]["builds"] = {}

        if self["format"] == "1.1.1":
            self["format"] = "2.0.0"

        for entry in ("admin", "scriptor", "vi"):
            if not self["default"]["builds"]:
                self["default"]["builds"]
            if entry in self["default"]:
                version_value = self["default"][entry].lstrip("v")
                self["default"]["builds"][entry] = {
                    "command": f"viur install {entry}",
                    "kind": "exec",
                    "version": version_value
                }
                del self["default"][entry]

        if "admin" in self["default"]["builds"] and "vi" in self["default"]["builds"]:
            echo_info(f"It seems like you have an Admin and a Vi Version in your project.json. \n"
                      f"per default the VI version will be overwritten by the viur-admin \n"
                      f"if you want to keep your vi press 'n'")
            if click.confirm(text=f"Do you want to use admin?", default=True):
                del self["default"]["builds"]["vi"]
            else:
                del self["default"]["builds"]["admin"]

        """
             Fetch the version of the 'viur-core' package.

             This method is responsible for fetching the version of the 'viur-core' package using 'pip list' and updating
             the project configuration accordingly.

             :return: None
        """
        try:
            result = os.popen('pip list --format=json').read()
            core_version = [x for x in json.loads(result) if x["name"] == "viur-core"][0]["version"]
            self["default"]["core"] = core_version

        except:
            self["default"]["core"] = "submodule"

        # conf updates must increase format version
        self.save()

config = ProjectConfig()
