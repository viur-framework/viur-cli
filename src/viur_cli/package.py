import os
import shutil
import zipfile
import click
import requests
from .conf import config
from pathlib import Path
from urllib.request import urlretrieve
from .cli import cli
from .utils import echo_success, echo_fatal, echo_error, echo_info

REPOS = {
    "vi": ("viur-framework/viur-vi", "viur-vi.zip"),
    "admin": ("viur-framework/vi-admin", "viur-vi.zip"),
    "scriptor": ("viur-framework/viur-scriptor", "source.zip"),
}


def get_version_info(software: str, version: str) -> tuple[str, str]:
    """Resolve a version label into a concrete `(version, download_url)` tuple.

    Calls the GitHub Releases API to validate that the requested tag
    exists and to translate ``"latest"`` into the corresponding semver.
    On success, also writes the resolved version into ``project.json``
    under ``default.builds[<software>]`` so subsequent installs are
    reproducible.

    Args:
        software: One of the keys in :data:`REPOS` (``vi``, ``admin``,
            ``scriptor``).
        version: A semver string (with or without a leading ``v``) or
            the literal ``"latest"``.

    Returns:
        Tuple ``(real_version, download_url)``. ``real_version`` may be
        ``None`` if the GitHub API request failed; the function falls
        back to the unvalidated ``version`` for the URL in that case.
    """
    repo, download_name = REPOS[software]

    if version[0] == "v":
        echo_info("Version should be provided without a leading \"v\"!")
        version = version[1:]  # normalize it!

    if version == "latest":
        url = f"https://api.github.com/repos/{repo}/releases/latest"
    else:
        url = f"https://api.github.com/repos/{repo}/releases/tags/v{version}"

    if not (req := requests.get(url)).ok:
        echo_error(f"Error while fetching version info (request failed): {req.status_code} {req.reason}")
        real_version = None  # Unknown
    else:
        # It's a validated and real existing version, so save it the project.json if necessary!
        real_version: str = req.json()["name"]
        version_str = real_version.lstrip("v")

        if software not in config["default"]["builds"]:
            config["default"]["builds"][software] = {
                "kind": "exec",
                "command": f"viur package install {software} {version_str if version != 'latest' else ''}".strip()
            }

        if config["default"]["builds"].get("version") != version_str:
            config["default"]["builds"][software]["version"] = version_str
            config.save()

    if not real_version and version == "latest":
        download_url = f"https://github.com/{repo}/releases/latest/download/{download_name}"
    else:
        # if the request before didn't failed, we use always the version
        tag = real_version if real_version else f"v{version}"
        download_url = f"https://github.com/{repo}/releases/download/{tag}/{download_name}"

    return real_version, download_url


_DEPRECATION_REMOVED_IN = "v3.2"


def _run_op(operation: str, component: str, profile: str, version: str = "latest") -> None:
    """Shared dispatch for the package install/update commands.

    Used by the deprecated ``viur package …`` command as well as the new
    ``viur admin/vi/scriptor …`` command groups so both paths exercise
    the exact same install logic.

    Args:
        operation: Either ``"install"`` or ``"update"``.
        component: ``vi``, ``admin``, ``scriptor``, or ``all``. ``all``
            on ``install`` covers admin + scriptor (vi must be requested
            explicitly); on ``update`` it iterates every entry in the
            profile's ``builds``.
        profile: Profile name from ``project.json``.
        version: Used only for single-component installs. Defaults to
            ``"latest"``.
    """
    conf = config.get_profile(profile)
    handlers = {"vi": _install_vi, "admin": _install_admin, "scriptor": _install_scriptor}

    def perform(comp: str, ver: str) -> None:
        if operation == "install":
            handlers[comp](ver, target=comp, profile=profile)
        else:  # update
            handlers[comp](version="latest", target=comp, profile=profile)

    if component == "all":
        if operation == "update":
            for build in conf["builds"]:
                if build in handlers:
                    perform(build, "latest")
        else:
            # The new admin replaces vi by default — vi only on explicit install.
            for build in ["admin", "scriptor"]:
                perform(build, "latest")
    else:
        perform(component, version)


@cli.command()
@click.argument("operation", type=click.Choice(["update", "install"]))
@click.argument("component", type=click.Choice(["vi", "admin", "scriptor", "all"]))
@click.argument("version", default="latest")
@click.argument("profile", default="default")
def package(operation, component, profile, version):
    """[DEPRECATED] Use 'viur <component> <operation>' instead.

    The 'viur package …' surface is kept for backwards compatibility and
    will be removed in v3.2. Prefer 'viur admin install', 'viur scriptor
    update', etc.
    """
    new_form = (
        f"viur {component} {operation}"
        + (f" {version}" if operation == "install" and version != "latest" else "")
    )
    click.echo(
        click.style(
            f"⚠ DEPRECATED: 'viur package {operation} {component}' will be removed in {_DEPRECATION_REMOVED_IN}. "
            f"Use '{new_form}' instead.",
            fg="yellow",
        ),
        err=True,
    )
    _run_op(operation, component, profile, version)


# ---- New semantic command groups ---------------------------------------

@cli.group()
def admin():
    """Manage the admin Vue.js CMS bundle."""


@admin.command(name="install")
@click.argument("version", default="latest")
@click.argument("profile", default="default")
def admin_install(version, profile):
    """Install or replace admin at the given version (default: latest)."""
    _run_op("install", "admin", profile, version)


@admin.command(name="update")
@click.argument("profile", default="default")
def admin_update(profile):
    """Update admin to the latest version."""
    _run_op("update", "admin", profile, "latest")


@cli.group()
def vi():
    """Manage the legacy 'vi' frontend bundle."""


@vi.command(name="install")
@click.argument("version", default="latest")
@click.argument("profile", default="default")
def vi_install(version, profile):
    """Install or replace vi at the given version (default: latest)."""
    _run_op("install", "vi", profile, version)


@vi.command(name="update")
@click.argument("profile", default="default")
def vi_update(profile):
    """Update vi to the latest version."""
    _run_op("update", "vi", profile, "latest")


@cli.group()
def scriptor():
    """Manage the scriptor frontend asset bundle.

    Asset-bundle install for the SPA shipped alongside admin. Not to be
    confused with ``viur script`` (which pulls/pushes Scriptor scripts
    against a deployed app).
    """


@scriptor.command(name="install")
@click.argument("version", default="latest")
@click.argument("profile", default="default")
def scriptor_install(version, profile):
    """Install or replace the scriptor frontend at the given version."""
    _run_op("install", "scriptor", profile, version)


@scriptor.command(name="update")
@click.argument("profile", default="default")
def scriptor_update(profile):
    """Update the scriptor frontend to the latest version."""
    _run_op("update", "scriptor", profile, "latest")


def checkreturncode(output):
    """Echo success or abort fatally based on a CompletedProcess's returncode."""
    if output.returncode == 0:
        echo_success("update was successful")
    else:
        echo_fatal("update exited with a non zero success code")


def _install_scriptor(version, target, profile):
    """Download the Scriptor frontend bundle and extract it into the deploy folder.

    Args:
        version: Semver string or ``"latest"``.
        target: Subfolder name under ``conf['distribution_folder']``
            (typically ``"scriptor"``).
        profile: Profile from ``project.json`` used to resolve
            ``distribution_folder``.
    """
    conf = config.get_profile(profile)
    dist_folder = conf["distribution_folder"]

    real_version, download_url = get_version_info("scriptor", version)

    scriptor_path = Path(dist_folder, target)
    tmp_zip_file = Path("scriptor.zip")

    def step_label(step: int) -> str:
        if step == 1:
            return f"downloading scriptor..."
        elif step == 1:
            return f"clearing scriptor..."
        elif step == 2:
            return f"extracting scriptor..."
        elif step == 4:
            return f"success!"

    with click.progressbar([1, 2, 3, 4], label="updating scriptor...", item_show_func=step_label) as bar:
        for element in bar:
            match element:
                case 1:
                    urlretrieve(download_url, tmp_zip_file)
                case 2:
                    if os.path.exists(scriptor_path):
                        shutil.rmtree(scriptor_path)
                case 3:
                    with zipfile.ZipFile(tmp_zip_file) as zip_f:
                        zip_f.extractall()
                case 4:
                    tmp_zip_file.unlink()
                    bar.label = "updated successful"

    echo_success(f"Installed admin {real_version}")


def _install_admin(version: str, target: str, profile: str = "default"):
    """Download the admin Vue.js CMS bundle and extract it into the deploy folder.

    Args:
        version: Semver string or ``"latest"``.
        target: Subfolder name under ``conf['distribution_folder']``
            (typically ``"admin"``).
        profile: Profile from ``project.json``.
    """
    conf = config.get_profile(profile)
    dist_folder = conf["distribution_folder"]

    real_version, download_url = get_version_info("admin", version)

    admin_path = Path(dist_folder, target)
    tmp_zip_file = Path("vi-admin.zip")

    def step_label(step: int) -> str:
        if step == 1:
            return f"downloading admin..."
        elif step == 2:
            return f"remove old admin..."
        elif step == 3:
            return f"extracting new admin..."
        elif step == 4:
            return f"success!"

    with click.progressbar([1, 2, 3, 4], label="updating admin...", item_show_func=step_label) as bar:
        for element in bar:
            if element == 1:
                urlretrieve(download_url, tmp_zip_file)
            elif element == 2:
                if os.path.exists(admin_path):
                    shutil.rmtree(admin_path)
            elif element == 3:
                with zipfile.ZipFile(tmp_zip_file) as zip_f:
                    zip_f.extractall(admin_path)
            elif element == 4:
                tmp_zip_file.unlink()
                bar.label = "updated successful"

    echo_success(f"Installed admin {real_version}")


def _install_vi(version, target, profile):
    """Download the legacy `vi` frontend bundle and extract it into the deploy folder.

    Args:
        version: Semver string or ``"latest"``.
        target: Subfolder name under ``conf['distribution_folder']``
            (typically ``"vi"``).
        profile: Profile from ``project.json``.
    """

    conf = config.get_profile(profile)
    dist_folder = conf["distribution_folder"]

    real_version, download_url = get_version_info("vi", version)

    vi_path = Path(dist_folder, target)
    tmp_zip_file = Path("vi.zip")

    def step_label(step: int) -> str:
        if step == 1:
            return f"downloading {version} vi..."
        elif step == 2:
            return f"remove old vi..."
        elif step == 3:
            return f"extracting new vi..."
        elif step == 4:
            return f"success!"

    with click.progressbar([1, 2, 3, 4], label="updating vi...", item_show_func=step_label) as bar:
        for element in bar:
            if element == 1:
                urlretrieve(download_url, tmp_zip_file)
            elif element == 2:
                if os.path.exists(vi_path):
                    shutil.rmtree(vi_path)
            elif element == 3:
                with zipfile.ZipFile(tmp_zip_file) as zip_f:
                    zip_f.extractall(vi_path)
            elif element == 5:
                tmp_zip_file.unlink()
                bar.label = "updated successful"

    echo_success(f"Installed vi {real_version}")
