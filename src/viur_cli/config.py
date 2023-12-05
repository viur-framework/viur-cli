import json
import click
from .utils import *


project_config_file_path = "project.json"


class ProjectConfig:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self, path=None):
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

        if not path:
            path = project_config_file_path

            echo_error("NOT PATH")

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
            project_config = json.loads(f.read())

        except FileNotFoundError:
            echo_fatal(f"Can't open {path} for reading")

        except json.decoder.JSONDecodeError as e:
            echo_fatal(f"The configuration in {path} contains invalid JSON: {str(e)}. Please verify right syntax.")

        return project_config

    def save_config(conf, path=None):
        """
        Write the current projectConfig dictionary to project.json.

        This function is used to write the current project configuration, provided as a dictionary,
        to the project.json file.

        :param conf: dict
            The project configuration to be written to the project.json file.

        :param path: str, optional
            The path to the project.json file. If not provided, the default projectConfigFilePath is used.

        :return: None
        """
        global project_config

        project_config = conf

        if not path:
            path = project_config_file_path

        f = open(path, "w")
        f.write(json.dumps(conf, indent=4, sort_keys=True))
        f.close()

    # New get_config
    @classmethod
    def get_instance(cls):

        # Access the singleton instance
        if not cls._instance:
            cls._instance = cls()

        return cls._instance

    def add_to_config(self):
        """
        Add a new configuration to project.json.

        This method allows the addition of a new configuration to the project.json file.
        It prompts for the configuration name, application name, and version.

        :return: None
        """
        if not self.config:
            return

        new_config = {
            click.prompt('name'): {
                "application_name": click.prompt('application name'),
                "version": click.prompt('develop version name')
            }
        }

        self.config.update(new_config)
        self.save_config()

    def remove_from_config(self):
        """
        Remove a configuration from project.json.

        This method allows the removal of an existing configuration from the project.json file.
        It prompts for the configuration name to remove.

        :return: None
        """
        configname = click.prompt('name')
        try:
            del self.config[configname]
            self.save_config()
        except KeyError:
            raise click.ClickException(click.style(f"{configname} not found", fg="red"))

    def fetch_core_version(self):
        """
        Fetch the version of the 'viur-core' package.

        This method is responsible for fetching the version of the 'viur-core' package using 'pip list' and updating
        the project configuration accordingly.

        :return: None
        """
        try:
            result = os.popen('pip list --format=json').read()
            core_version = [x for x in json.loads(result) if x["name"] == "viur-core"][0]["version"]

            if "default" not in self.config:
                self.config["default"] = {}

            self.config["default"]["core"] = core_version
            self.save_config()
        except Exception as e:
            if self.config and "default" in self.config:
                self.config["default"]["core"] = "submodule"
                self.save_config()
                raise click.ClickException(click.style(f"Error fetching core version: {str(e)}", fg="red"))

    def versions_to_builds(self, version_list):
        """
        Convert versions in the configuration to builds.

        This method iterates through the provided version list and updates the project configuration
        by converting versions to builds.

        :param version_list: list
            List of versions to convert to builds.
        :return: None
        """
        for entry in version_list:
            if entry in self.config.get("default", {}):
                if self.config["default"][entry]:
                    version_value = self.config["default"][entry].lstrip("v")
                    self.config["default"]["builds"][entry] = {
                        "command": f"viur install {entry}",
                        "kind": "exec",
                        "version": version_value
                    }
                    del self.config["default"][entry]
        self.save_config()

    def update_config(self, path=None):
        """
        Update the project configuration.

        This method performs updates and migrations on the project configuration as needed. It includes version checks
        and format updates. Ensure that 'load_config()' is called before invoking this method.

        :param path: str, optional
            The path to the project.json file. If not provided, the root directory of the project is used.

        :return: None
        """
        assert self.config, "load_config() must be called first!"

        assert self.config["format"] in ["1.0.0", "1.0.1", "1.1.0", "1.1.1", "1.2.0"], \
            "Invalid formatversion, you have to fix it manually"

        if "format" not in self.config:
            self.config["format"] = "1.0.1"

        # Version 1.0.1
        if (pyodide_version := self.config["default"].get("pyodide")) and pyodide_version.startswith("v"):
            self.config["default"]["pyodide"] = pyodide_version[1:]  # remove v prefix

        if self.config["format"] == "1.0.0":
            self.config["format"] = "1.0.1"

        # Version 1.1.1
        if self.config["format"] == "1.1.0":
            self.config["format"] = "1.1.1"
            builds = self.config["default"].get("builds", {}).copy()
            for k, v in builds.items():
                if builds[k]["kind"] == "script":
                    builds[k]["kind"] = "exec"
            self.config["default"]["builds"] = builds

        # Version 1.2.0
        version_list = ["admin", "scriptor", "vi"]

        self.versions_to_builds(version_list)

        if "admin" in self.config["default"]["builds"] and "vi" in self.config["default"]["builds"]:
            echo_info(f"It seems like you have an Admin and a Vi Version in your project.json. \n"
                      f"per default the VI version will be overwritten by the viur-admin \n"
                      f"if you want to keep your vi press 'n'")
            if click.confirm(text=f"Do you want to use admin?", default=True):
                del self.config["default"]["builds"]["vi"]
            else:
                del self.config["default"]["builds"]["admin"]

        # conf updates must increase format version
        self.save_config()
