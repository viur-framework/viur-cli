import json
import click
from .utils import *
from copy import deepcopy

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
            echo_fatal(
                f"The configuration in {PROJECT_CONFIG_FILE} contains invalid JSON: {str(e)}. Please verify right syntax.")

        self.migrate()

    def save(self):
        """
        Write the current projectConfig dictionary to project.json.
        """
        with open(PROJECT_CONFIG_FILE, "w") as f:
            json.dump(self, f, indent=4, sort_keys=True)
            f.write('\n')

    def get_profile(self, profile):
        """Get profile configuration"""
        if profile == "format":
            echo_fatal("Your profile can not be named 'Format' ")
        if profile not in self:
            echo_fatal(f"{profile!r} is not a valid profile name")
        return self["default"].copy() | self[profile]

    def delete(self):
        """Delete profile cofniguration"""
        configname = click.prompt('name')
        try:
            del self[configname]
            self.save()
        except:
            raise click.ClickException(click.style(f"{configname} not found", fg="red"))

    def find_key(self, dictionary, target_key, target, level=0):
        if target_key in dictionary:
            value = dictionary[target_key]

            if target is None:
                self[target_key] = value
                del value
                return
            else:
                self[target][target_key] = value
                return

        for value in list(dictionary.values()):
            if isinstance(value, dict):
                self.find_key(value, target_key, target, level=level + 1)

    def migrate(self):

        if "application_name" not in self["default"]:
            self.find_key(self, target_key="application_name", target="default")
            if "application_name" in self:
                del self["application_name"]

        #check if core is in any profile
        if "core" not in self:
            self.find_key(self, target_key="core", target="default", level=0)


        if old_format := self["default"].get("format"):
            self["format"] = old_format
            del self["default"]["format"]

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
            format_version_updated = True
        else:
            format_version_updated = False

        for entry in ("admin", "scriptor", "vi"):
            if not self["default"]["builds"]:
                self["default"]["builds"]
            if entry in self["default"]:
                version_value = self["default"][entry].lstrip("v")
                self["default"]["builds"][entry] = {
                    "command": f"viur package install {entry}",
                    "kind": "exec",
                    "version": version_value
                }
                del self["default"][entry]

        if format_version_updated:
            response = click.prompt(
                text="Do you want to enforce use of admin only? (yes/no/keep)",
                type=click.Choice(["yes", "no", "keep"]),
                default="yes"
            )

            if response == "yes":
                try:
                    del self["default"]["builds"]["vi"]
                except:
                    echo_info("You are using the ViUR Admin")
            elif response == "no":
                try:
                    del self["default"]["builds"]["admin"]
                except:
                    echo_info("You are using the Vi Administration")
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
