import os
import shutil
import click
import sys
import typing
import datetime
import getpass


def rmdir(dir):
    """Secure and error-prone recursive removal of entire folders.

    Does only allow to remove folders inside the project folder, so that a misconfiguration, wanted or not,
    cannot delete the entire home folder or similar.
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
    """Performs an os.system() call with the given command, but throws an echo_fatal on error and stops viur-cli."""
    if os.system(cmd) != 0:
        echo_fatal(f"Failed to execute {cmd!r}")


def echo_error(msg):
    """colored cli feedback"""
    click.echo(click.style("ERROR: " + msg, fg="red"))


def echo_positive(msg):
    """colored cli feedback"""
    click.echo(click.style("INFO: " + msg, fg="green"))


def echo_warning(msg):
    """colored cli feedback"""
    click.echo(click.style("WARNING: " + msg, fg=(255, 231, 0)))


def echo_fatal(msg):
    echo_error(msg)
    sys.exit(1)


def echo_info(msg):
    """colored cli feedback"""
    click.echo(click.style(msg, fg="cyan"))


def replace_vars(string: str, vars: typing.Optional[typing.Dict[str, str]] = None) -> str:
    """Replaces $(placeholders) in a string by values from a dict until no more values are being replaced.

    The function enriches the provided vars dictionary by the following defaults if not given:
    - user: Current user's name
    - day: Current date's day
    - month: Current date's month
    - year: Current date's year
    - hour: Current date's hour
    - minute: Current date's minute
    - second: Current date's second
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

    return string


def requirements_to_dict(requirements):
    ret = {}
    for requirement in requirements:
        package, version = requirement.requirement.split(";")[0].split("==")
        package = package.split("[")[0]

        requirement.options.update({"version": version.strip()})
        ret.update({package.lower(): requirement.options})
    return ret
