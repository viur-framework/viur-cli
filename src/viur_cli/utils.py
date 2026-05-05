import os
import shutil
import click
import sys
import typing
import datetime
import getpass
import subprocess


def rmdir(dir):
    """Recursively remove a folder, but only if it lives under the current working directory.

    Refuses (via ``echo_fatal``) to delete anything outside the project
    so a misconfigured ``project.json`` can't take out ``$HOME`` or
    similar. Missing directories are silently ignored.
    """
    # Verify the dir is part of the current folder
    dir = os.path.abspath(dir)
    wdir = os.getcwd()
    if wdir != os.path.commonpath((wdir, dir)):
        echo_fatal(f"Illegal path configuration, won't remove {dir!r}")

    # Remove it
    try:
        shutil.rmtree(dir)
    except FileNotFoundError:
        pass


def system(cmd):
    """Run a shell command and abort viur-cli on non-zero exit.

    Still uses ``shell=True`` because callers pass chained shell strings
    (e.g. ``cd src && npm install && npm run build``). The build
    pipeline refactor is the right place to switch this to argv lists;
    until then this wrapper at least replaces the older ``os.system``
    with ``subprocess.run``.
    """
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        echo_fatal(f"Failed to execute {cmd!r} (exit {result.returncode})")


def echo_error(msg):
    """Print a red ERROR-prefixed line."""
    click.echo(click.style("ERROR: " + msg, fg="red"))


def echo_success(msg):
    """Print a green SUCCESS-prefixed line."""
    click.echo(click.style("SUCCESS: " + msg, fg="green"))


def echo_warning(msg):
    """Print a yellow WARNING-prefixed line."""
    click.echo(click.style("WARNING: " + msg, fg=(255, 231, 0)))


def echo_fatal(msg):
    """Print an ERROR line and exit the process with status 1."""
    echo_error(msg)
    sys.exit(1)


def echo_info(msg):
    """Print a cyan informational line."""
    click.echo(click.style(msg, fg="cyan"))


def replace_vars(string: str, vars: typing.Optional[typing.Dict[str, str]] = None) -> str:
    """Replace `$(placeholder)` tokens in a string until no more are resolvable.

    Args:
        string: Template string containing zero or more ``$(name)``
            tokens.
        vars: Mapping of token names to replacement values. Mutated in
            place to gain a small set of defaults if not already
            present:

            * ``user`` — current OS user (or ``"viur"`` as fallback)
            * ``day`` / ``month`` / ``year`` / ``hour`` / ``minute`` /
              ``second`` — zero-padded components of the current
              datetime

    Returns:
        The fully expanded string. Iterates until a fixed point so
        nested expansions resolve. ``$(ref)`` is special-cased to the
        short git HEAD SHA (resolved at call time).
    """
    # set some defaults
    if vars is None:
        vars = {}

    # current user
    if "user" not in vars:
        try:
            whoami = getpass.getuser()
        except:
            whoami = "viur"

        vars["user"] = whoami

    # date values
    now = datetime.datetime.now()
    for item in ["day", "month", "year", "hour", "minute", "second"]:
        if item not in vars:
            vars[item] = "%02d" % getattr(now, item)

    # replaces variables until string doesn't change anymore.
    old_string = ""

    while old_string != string:
        old_string = string
        for var, content in vars.items():
            string = string.replace(f"$({var})", str(content))
    if "$(ref)" in string:
        ref = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
        string = string.replace("$(ref)", ref)
    return string


def requirements_to_dict(requirements):
    """Convert a list of pipfile-requirements entries into a `{package: options}` dict.

    Each input entry is expected to expose ``.requirement`` (e.g.
    ``foo[extra]==1.2.3; python_version>="3.11"``) and an
    ``.options`` dict. The resulting dict is keyed by package name
    (lower-cased, extras stripped) and carries the parsed version under
    a new ``"version"`` key inside the options dict.
    """
    ret = {}
    for requirement in requirements:
        package, version = requirement.requirement.split(";")[0].split("==")
        package = package.split("[")[0]

        requirement.options.update({"version": version.strip()})
        ret.update({package.lower(): requirement.options})
    return ret
