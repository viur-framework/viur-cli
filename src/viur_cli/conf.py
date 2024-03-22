import json
import click
import requests
import difflib
from .utils import *
from .version import __version__ as cli_version

PROJECT_CONFIG_FILE = "project.json"
PROJECT_CONFIG_VERSION = "2.0.0"
LAST_VERSION = ""


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

    def migrate(self):
        if old_format := self["default"].get("format"):
            self["format"] = old_format
            del self["default"]["format"]

        assert self["format"] in ["1.0.0", "1.0.1", "1.1.0", "1.1.1", "1.2.0", PROJECT_CONFIG_VERSION], \
            "Invalid formatversion, you have to fix it manually"

        # Version 1.0.1
        if (pyodide_version := self["default"].get("pyodide")) and pyodide_version.startswith("v"):
            self["default"]["pyodide"] = pyodide_version[1:]  # remove v prefix

        if not self.get("cli-version"):
            print_changelog_from_github('viur-framework', 'viur-cli', None)
            self["cli-version"] = cli_version

        elif self.get("cli-version") != cli_version:
            print_changelog_from_github('viur-framework', 'viur-cli', self.get("cli-version"))
            self["cli-version"] = cli_version

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
                del self["default"]["builds"]["vi"]
            elif response == "no":
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


def print_changelog_from_github(user, repo, last_version):
    version_url = f"https://raw.githubusercontent.com/{user}/{repo}/main/CHANGELOG.md"
    response = requests.get(version_url)

    if last_version is not None:
        version_url1 = f"https://raw.githubusercontent.com/{user}/{repo}/{last_version}/CHANGELOG.md"
        echo_warning(version_url1)
        response1 = requests.get(version_url1)

    if last_version is None and response.ok:
        changelog_lines = response.text.split("\n")[:20]
        echo_info("It seems you have updated your viur-cli!\n "
                  "Please consider reading the changelog: https://github.com/viur-framework/viur-cli/blob/main/CHANGELOG.md")
        click.echo("\n".join(changelog_lines))
        click.confirm("Done?", default=True)

    elif response.ok and response1.ok:
        get_changelog_difference(response.text.split('\n'), response1.text.split('\n'))

    else:
        echo_error("Unable to fetch the changelog.")


def get_changelog_difference(response, response1):
    diff = difflib.unified_diff(response, response1)
    for line in diff:  # Skip the first 2 lines
        if line.startswith('@@') or line.startswith('---') or line.startswith('+++'):
            continue
        echo_info(line[1:])


config = ProjectConfig()
