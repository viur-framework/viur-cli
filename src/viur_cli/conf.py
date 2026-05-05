import json
import click
import requests
import difflib
import os
from .utils import *
from .version import __version__ as cli_version


class Config(dict):
    """Dict-backed JSON config file with parent-dir auto-discovery and a migration hook.

    Subclasses set :attr:`FILENAME` to the on-disk filename (e.g.
    ``project.json``) and :attr:`VERSION` to the schema version they
    expect. On instantiation the loader walks up the directory tree
    until it finds the file, reads + parses it, and runs
    :meth:`migrate` for any per-version rewrites.
    """

    FILENAME: str | None = None
    """On-disk filename to read/write (set by subclasses)."""

    VERSION: str | None = None
    """Schema version this config layer understands. Tied to the viur-cli release."""

    def __init__(self, *, path=None):
        self.path = path

        if self.VERSION:
            self["format"] = self.VERSION

        self.load()

    def load(self):
        """Walk up the directory tree to find FILENAME, then read + migrate it.

        Side effects:
            * ``os.chdir("..")`` repeatedly until ``FILENAME`` is found
              or the filesystem root is reached. The resulting cwd
              becomes the project root for all subsequent commands.
            * Aborts via ``echo_fatal`` if the file is missing, broken
              JSON, or otherwise unreadable.
            * Calls :meth:`migrate` on success so subclasses can rewrite
              older formats.
        """
        # Search in any parent folder for a project.json,
        # change working directory because subsequent commands
        # require for project root folder.

        changed = False
        while not os.path.exists(self.FILENAME):
            os.chdir("..")
            changed = True

            if os.getcwd() == "/":

                if self.path:
                    self.save()
                    self.load()
                    return
                else:
                    echo_fatal(f"{self.FILENAME} not found - please check if you are in the right folder.")

        if changed:
            echo_info(f"Project root is {os.getcwd()}")

        try:
            f = open(self.FILENAME, "r")
            self.path = os.getcwd()
            self.update(json.loads(f.read()))


        except FileNotFoundError:
            echo_fatal(f"Can't open {self.FILENAME} for reading")

        except json.decoder.JSONDecodeError as e:
            echo_fatal(
                f"The configuration in {self.FILENAME} contains invalid JSON: {str(e)}. Please verify right syntax.")

        self.migrate()

    def migrate(self):
        """Hook for subclasses to rewrite older format versions in place."""
        pass

    def save(self):
        """Persist the current dict back to FILENAME as pretty-printed JSON."""
        os.chdir(self.path)
        with open(self.FILENAME, "w") as f:
            json.dump(self, f, indent=4, sort_keys=True)
            f.write('\n')


class ProjectConfig(Config):
    FILENAME = "project.json"
    VERSION = "2.0.0"

    def __init__(self):
        self["default"] = {}
        super().__init__()

    def get_profile(self, profile):
        """Return the merged config for `profile` (default overlaid with profile-specific keys).

        Args:
            profile: A profile key from ``project.json``. Must not be
                ``"format"`` (reserved for the schema version field).

        Aborts via ``echo_fatal`` on an unknown profile name.
        """
        if profile == "format":
            echo_fatal("Your profile can not be named 'Format' ")
        if profile not in self:
            echo_fatal(f"{profile!r} is not a valid profile name")
        return self["default"].copy() | self[profile]

    def find_key(self, dictionary, target_key, target, keep=False):
        if target_key in dictionary:
            if keep:
                value = dictionary[target_key]
            else:
                value = dictionary.pop(target_key)
            if not target:
                self[target_key] = value
            else:
                self.setdefault(target, {})[target_key] = value
        else:
            for value in list(dictionary.values()):
                if isinstance(value, dict):
                    self.find_key(value, target_key, target, keep=keep)

    def remove_key(self, dictionary, target_key):
        if target_key in dictionary:
            del dictionary[target_key]

        for value in list(dictionary.values()):
            if isinstance(value, dict):
                self.remove_key(value, target_key)

    def migrate(self):

        if "application_name" not in self["default"]:
            self.find_key(self, target_key="application_name", target="default", keep=True)
            if "application_name" in self:
                del self["application_name"]

        if "version" not in self["default"]:
            self.find_key(self, target_key="version", target="default", keep=True)
            # Fail Safe
            if "version" in self:
                del self["version"]
        self.remove_key(self, target_key="core")

        if old_format := self["default"].get("format"):
            self["format"] = old_format
            del self["default"]["format"]

        assert self["format"] in ["1.0.0", "1.0.1", "1.1.0", "1.1.1", "1.2.0", self.VERSION], \
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

        # Check if Builds is in the project.json
        if "builds" not in self["default"].keys():
            self["default"]["builds"] = {}

        if self["format"] == "1.1.1":
            self["format"] = "2.0.0"
            format_version_updated = True
        else:
            format_version_updated = False

        for entry in ("admin", "scriptor", "vi"):
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
                self["default"]["builds"].pop("vi", None)
                echo_info("You are using the ViUR Admin")
            elif response == "no":
                self["default"]["builds"].pop("admin", None)
                echo_info("You are using the Vi Administration")

        self.save()


def print_changelog_from_github(user, repo, last_version):
    """Fetch CHANGELOG.md from GitHub and either print it or diff it against `last_version`.

    On a fresh install (``last_version is None``) the first 20 lines of
    ``main``'s ``CHANGELOG.md`` are printed and the user is prompted to
    acknowledge. On an upgrade, the diff between ``v{last_version}``
    and ``main`` is rendered via :func:`get_changelog_difference`.
    """
    version_url = f"https://raw.githubusercontent.com/{user}/{repo}/refs/heads/main/CHANGELOG.md"
    response = requests.get(version_url)

    if last_version is not None:
        version_url1 = f"https://raw.githubusercontent.com/{user}/{repo}/refs/tags/v{last_version}/CHANGELOG.md"
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
    """Print the unified diff between two changelog line lists, hiding diff metadata."""
    diff = difflib.unified_diff(response, response1)
    for line in diff:  # Skip the first 2 lines
        if line.startswith('@@') or line.startswith('---') or line.startswith('+++'):
            continue
        echo_info(line[1:])


class ScriptorConfig(Config):
    """Persistent settings for `viur script` (base URL, username, working dir, cookies)."""
    # TODO: merge with the project-level Config layout
    FILENAME = "viur_scriptor_config.json"
    DEFAULT_BASE_URL = "http://localhost:8080"
    DEFAULT_WORKING_DIR = "scripts/"

    def __init__(self, **kwargs):
        self.update({
            "base_url": self.DEFAULT_BASE_URL,
            "working_dir": self.DEFAULT_WORKING_DIR,
        })
        super().__init__(**kwargs)


# Create specific configs.
# v3 transitional patch: ProjectConfig() / ScriptorConfig() call sys.exit(1)
# at module import time when project.json is missing. We swallow the SystemExit
# so module import succeeds outside a viur project (e.g. for `viur --help`).
# Stderr is redirected during the call so the auto-init's "project.json not
# found" message doesn't spam every CLI invocation. Consumers that actually
# use these globals will hit the original error path on first access — that's
# the right place to surface the message. The proper fix (lazy / dataclass
# config) is deferred to a later branch.
import contextlib as _contextlib
import io as _io

with _contextlib.redirect_stderr(_io.StringIO()), _contextlib.redirect_stdout(_io.StringIO()):
    try:
        config = ProjectConfig()
        scriptor_config = ScriptorConfig(path=config.path)
    except SystemExit:
        config = None
        scriptor_config = None
