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

    get_version_info(software: str, version: str) -> tuple[str, str]

    Retrieves version information for a software from a given repository.

    Parameters:
    - software: A string representing the name of the software.
    - version: A string representing the version of the software.

    Returns:
    A tuple containing the real version (str) and the download URL (str) for the software.

    Note:
    - The version should be provided without a leading "v".
    - If the version is set to "latest", the latest release information and download URL will be fetched.
    - If the version is a valid existing release, the real version will be saved to the config.
    - If the version is not a valid existing release, the real_version will be None (Unknown).
    - The download URL will be constructed based on the real_version and the download name for the software.

    Example Usage:
    real_version, download_url = get_version_info("sample_software", "1.2.3")

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
def packet(operation, component, profile, version):
    """
    This method is used to handle packet operations, such as updating or installing components.

    Parameters:
    - operation (str): The operation to perform. Must be either 'update' or 'install'.
    - component (str): The component to update or install. Must be one of: 'vi', 'admin', 'scriptor', 'all'.
    - profile (str, optional): The profile to use. Defaults to 'default'.
    - version (str, optional): The version of the component to update or install. Defaults to 'latest'.

    Note: The 'all' component option is only applicable to the 'update' operation.

    Examples:
    packet('update', 'vi') -> Updates 'vi' component to the latest version using the default profile.
    packet('install', 'admin', profile='prod', version='1.0') -> Installs 'admin' component with version '1.0' using the 'prod' profile.
    packet('update', 'all', version='2.0') -> Updates all components to version '2.0' using the default profile.

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
                    perform_operation(build, version)


def checkreturncode(output):
    """
    Checks the return code of a command execution and prints a message based on the return code.

    Parameters:
    - output: A subprocess.CompletedProcess object representing the output of a command execution.

    Returns:
    None

    """
    if output.returncode == 0:
        echo_positive("update was successful")
    else:
        echo_fatal("update exited with a non zero success code")


def scriptor(version, target, profile):
    """
    Update the Scriptor tool to the specified version.

    Parameters:
    - version (str): The version of Scriptor to update to.
    - target (str): The target directory for the updated Scriptor tool.
    - profile (str): The specific profile to use for configuration.

    Returns:
    None
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
    """
    Updates the admin tool to a specified version.

    Parameters:
        version (str): The version of the admin tool to update to.
        target (str): The target folder to update the admin tool in.
        profile: The profile to use for configuration.

    Returns:
        None

    Example Usage:
        admin("1.2.0", "C:/admin", "production")
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


def vi(version, target, profile):
    """
    Updates the version of vi based on the provided parameters.

    Parameters:
    - version (str): The version of vi to update to.
    - target (str): The target folder where vi will be installed.
    - profile (str): The profile to use for configuration.

    Returns:
    None

    Example:
    vi("1.2.3", "/path/to/vi", "production")
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
