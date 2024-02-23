import os
import shutil
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
    """

    :param software: String
        Name of the ViUR Software

    :param version: String
        Desired version of the ViUR Software

    :returns: tuple[str, str]
        real version and download URL

    Description:
    This method takes in the name of a software and a desired version,
    and returns the real version and download URL for that software.

    The 'software' parameter is a string that represents the name of the software.

    The 'version' parameter is a string that represents the desired version of the software.
    If the version starts with 'v', it will be normalized by removing the leading 'v'.
    *The 'version' can also be set as 'latest' to get the latest version available.

    The method uses the provided 'software' parameter to fetch the repository
    and download information from REPOS dictionary.

    If the 'version' is 'latest', the method constructs the URL using the repository information to fetch the
    latest release information from GitHub API. If the request fails, an error message
    * will be displayed. If the request is successful, the real version of the latest release is obtained
    and saved in the config.

    If the 'version' is not 'latest', the method constructs the URL using the repository and desired version information.
    If the request for the version tag information fails, the method
    * falls back to the previously obtained real version. Else, the tag is used to construct the download URL.

    Finally, the method returns a tuple containing the real version and download URL.

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


@cli.command()
@click.argument('operation', type=click.Choice(['update', 'install']))
@click.argument('component', type=click.Choice(['vi', 'admin', 'scriptor', 'all']))
@click.argument('profile', default='default')
@click.argument("version", default="latest")
def package(operation, component, profile, version):
    """
    Performs installements and updates of ViUR Ecosystem packages
    """
    conf = config.get_profile(profile)
    operations_links = {
        'vi': vi,
        'admin': admin,
        'scriptor': scriptor
    }

    def perform_operation(component, version):
        if operation == 'install':
            operations_links[component](version, target=component, profile=profile)
        else:
            operations_links[component](version="latest", target=component, profile=profile)

    match component:
        case 'vi':
            perform_operation('vi', version)
        case 'admin':
            perform_operation('admin', version)
        case 'scriptor':
            perform_operation('scriptor', version)
        case 'all':
            if operation == 'update':
                for build in conf["builds"]:
                    if build in operations_links:
                        perform_operation(build, "latest")
            else:
                # We want to force the User to use the new Admin, so Vi can only be installed explicitly!!
                for build in ["admin", "scriptor"]:
                    perform_operation(build, "latest")


def checkreturncode(output):
    """
    Check the return code of a process output.
    """
    if output.returncode == 0:
        echo_positive("update was successful")
    else:
        echo_fatal("update exited with a non zero success code")


def scriptor(version, target, profile):
    """
    Update the Scriptor tool to a specified version.
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


def admin(version: str, target: str, profile):
    """Update the admin to a specific version."""
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


def vi(version, target, profile):
    """Updates Vi to the specified version."""

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
