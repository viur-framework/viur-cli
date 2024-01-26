import os
import shutil
import subprocess
import zipfile
import click
import requests
from viur_cli import echo_positive, echo_fatal
from .conf import config
from pathlib import Path
from urllib.request import urlretrieve
from . import cli, echo_error, echo_info

REPOS = {
    "vi": ("viur-framework/viur-vi", "viur-vi.zip"),
    "admin": ("viur-framework/vi-admin", "viur-vi.zip"),
    "scriptor": ("viur-framework/viur-scriptor", "source.zip"),
}


def get_version_info(software: str, version: str) -> tuple[str, str]:
    """Validate the version name and return the download url.

    :param software: The key of a software in REPOS
    :param version: The version number entered by the user
    :return: A pair of the real version number and the download url
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
        # It's a validated and real existing version, save it to our config
        real_version: str = req.json()["name"]
        config["default"][software] = real_version.lstrip("v")
        config.save()

    if not real_version and version == "latest":
        download_url = f"https://github.com/{repo}/releases/latest/download/{download_name}"
    else:
        # if the request before didn't failed, we use always the version
        tag = real_version if real_version else f"v{version}"
        download_url = f"https://github.com/{repo}/releases/download/{tag}/{download_name}"

    return real_version, download_url


@cli.group()
def install():
    """
    Manage the installation of ViUR features.

    The 'install' command group provides various subcommands for managing the installation of ViUR features, including
    the ViUR administration interfaces and the scriptor IDE. You can choose to install specific versions or use the
    latest available versions.

    Example Usage:
    ```shell
    viur install vi --version v2.0.0
    viur install admin
    viur install scriptor --version latest
    ```

    Available subcommands:
    - 'vi': Install the legacy ViUR administration interface.
    - 'admin': Install the new ViUR administration interface.
    - 'scriptor': Install the scriptor IDE.

    Note:
    - When using the 'admin' subcommand, the new administration interface will be installed.
    - The 'scriptor' subcommand installs the scriptor IDE.
    - Ensure that you have a valid project configuration before using these subcommands.

    :return: None
    """


def checkreturncode(output):
    if output.returncode == 0:
        echo_positive("update was successful")
    else:
        echo_fatal("update exited with a non zero success code")


@install.command()
@click.argument("action", type=click.Choice(["vi", "admin", "scriptor", "all"]))
@click.argument("profile", default='default')
def update(action, profile):
    conf = config.get_profile(profile)

    """Updates all Viur Ecosystem Components"""
    if action == "all":
        # Get the builds of the project.json profile
        for build in conf["builds"]:
            echo_info(f"updating {build}...")
            output = subprocess.run(f"viur install {build} latest {profile}",
                                    capture_output=True, check=True, shell=True)
            checkreturncode(output)

    # This function is obsolete, howerver the user might expect this behaviour.
    else:
        output = subprocess.run(f"viur install {action} latest {profile}",
                                capture_output=True, check=True, shell=True)
        checkreturncode(output)


@install.command()
@click.argument("version", default="latest")
@click.argument("profile", default="default")
@click.option("--next", "-n", "next_", is_flag=True, default=False)
@click.option("--target", "-t", default="vi")
def vi(version, target, next_, profile):
    """Install the legacy ViUR administration interface.

    This subcommand allows you to install the legacy ViUR administration interface. You can specify a version to
    install, or use the latest available version. It includes a 'next' option for compatibility,
    but it is deprecated in favor of the 'admin' subcommand.

    :param version: str, default: 'latest'
        The version of the legacy ViUR administration interface to install.
        Use 'latest' for the latest available version.

    :param target: str, default: 'vi'
        The target folder where the ViUR administration interface will be installed.

    :param next_: bool, default: False
        A deprecated option, please use the 'admin' subcommand for the new administration interface.

    Example Usage:
    ```shell
    viur install vi --version v2.0.0 --target my-admin
    viur install vi --version latest
    ```

    The 'vi' subcommand downloads and installs the specified
    or latest version of the legacy ViUR administration interface.
    It updates the configuration with the installed version.

    :return: None
    """
    if next_:
        echo_info("DEPRECATED please use: viur install admin")
        return downloadadmin(version, target)

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
            return f"Editing Project.json"
        elif step == 5:
            return f"success!"

    with click.progressbar([1, 2, 3, 4, 5], label="updating vi...", item_show_func=step_label) as bar:
        for element in bar:
            if element == 1:
                urlretrieve(download_url, tmp_zip_file)
            elif element == 2:
                if os.path.exists(vi_path):
                    shutil.rmtree(vi_path)
            elif element == 3:
                with zipfile.ZipFile(tmp_zip_file) as zip_f:
                    zip_f.extractall(vi_path)
            elif element == 4:
                config.migrate()
            elif element == 5:
                tmp_zip_file.unlink()
                bar.label = "updated successful"


@install.command()
@click.argument("version", default="latest")
@click.argument("profile", default="default")
@click.option("--target", "-t", default="vi")
def admin(version, target, profile):
    """Install admin — the new ViUR administration interface."""
    return downloadadmin(version, target, profile)


def downloadadmin(version: str, target: str, profile):
    """
    Install the new ViUR administration interface.

    This subcommand allows you to install the new ViUR administration interface. You can specify a version to install,
    or use the latest available version.

    :param version: str, default: 'latest'
        The version of the new ViUR administration interface to install. Use 'latest' for the latest available version.

    :param target: str, default: 'vi'
        The target folder where the new ViUR administration interface will be installed.

    Example Usage:
    ```shell
    viur install admin --version v2.0.0 --target my-admin
    viur install admin --version latest
    ```

    The 'admin' subcommand downloads and installs the specified or latest version of the new
    ViUR administration interface.
    It updates the configuration with the installed version.

    :return: None
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
            return f"Editing Project.json"
        elif step == 5:
            return f"success!"

    with click.progressbar([1, 2, 3, 4, 5], label="updating admin...", item_show_func=step_label) as bar:
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
                config.migrate()
            elif element == 5:
                tmp_zip_file.unlink()
                bar.label = "updated successful"


@install.command()
@click.argument("version", default="latest")
@click.argument("profile", default="default")
@click.option("--target", "-t", default="scriptor")
def scriptor(version, target, profile):
    """
    Install the scriptor IDE.

    This subcommand allows you to install the scriptor IDE. You can specify a version to install, or use the latest
    available version.

    :param version: str, default: 'latest'
        The version of the scriptor IDE to install. Use 'latest' for the latest available version.

    :param target: str, default: 'scriptor'
        The target folder where the scriptor IDE will be installed.

    Example Usage:
    ```shell
    viur install scriptor --version v1.2.0 --target my-scriptor
    viur install scriptor --version latest
    ```

    The 'scriptor' subcommand downloads and installs the specified or latest version of the scriptor IDE.

    :return: None
    """
    conf = config.get_profile(profile)
    dist_folder = conf["distribution_folder"]

    real_version, download_url = get_version_info("scriptor", version)

    scriptor_path = Path(dist_folder, target)
    tmp_zip_file = Path("scriptor.zip")

    def step_label(step: int) -> str:
        if step == 1:
            return f"downloading scriptor..."
        elif step == 2:
            return f"extracting scriptor..."
        elif step == 3:
            return f"Editing Project.json"
        elif step == 4:
            return f"success!"

    with click.progressbar([1, 2, 3, 4], label="updating scriptor...", item_show_func=step_label) as bar:
        for element in bar:
            match element:
                case 1:
                    urlretrieve(download_url, tmp_zip_file)
                case 2:
                    with zipfile.ZipFile(tmp_zip_file) as zip_f:
                        zip_f.extractall()
                case 3:
                    config.migrate()
                case 4:
                    tmp_zip_file.unlink()
                    bar.label = "updated successful"
