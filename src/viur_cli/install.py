import os
import shutil
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

import click
import requests

from . import cli, echo_error, echo_info, get_config, write_config

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
        project_config = get_config()
        project_config["default"][software] = real_version.lstrip("v")
        write_config(project_config)

    if not real_version and version == "latest":
        download_url = f"https://github.com/{repo}/releases/latest/download/{download_name}"
    else:
        # if the request before didn't failed, we use always the version
        tag = real_version if real_version else f"v{version}"
        download_url = f"https://github.com/{repo}/releases/download/{tag}/{download_name}"

    return real_version, download_url


@cli.group()
def install():
    """Install ViUR features"""


@install.command()
@click.argument("version", default="latest")
@click.option("--next", "-n", "next_", is_flag=True, default=False)
@click.option("--target", "-t", default="vi")
def vi(version, target, next_):
    """Install vi — the legacy ViUR administration interface."""
    if next_:
        echo_info("DEPRECATED please use: viur install admin")
        return downloadadmin(version, target)

    projectConfig = get_config()
    dist_folder = projectConfig["default"]["distribution_folder"]

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
            elif element == 4:
                tmp_zip_file.unlink()
                bar.label = "updated successful"


@install.command()
@click.argument("version", default="latest")
@click.option("--target", "-t", default="vi")
def admin(version, target):
    """Install admin — the new ViUR administration interface."""
    return downloadadmin(version, target)


def downloadadmin(version: str, target: str):
    """download latest vi-admin or a specific version"""
    projectConfig = get_config()
    dist_folder = projectConfig["default"]["distribution_folder"]

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


@install.command()
@click.argument("version", default="latest")
@click.option("--target", "-t", default="scriptor")
def scriptor(version, target):
    """Install scriptor IDE."""
    projectConfig = get_config()
    dist_folder = projectConfig["default"]["distribution_folder"]

    real_version, download_url = get_version_info("scriptor", version)

    scriptor_path = Path(dist_folder, target)
    tmp_zip_file = Path("scriptor.zip")

    def step_label(step: int) -> str:
        if step == 1:
            return f"downloading scriptor..."
        elif step == 2:
            return f"extracting scriptor..."
        elif step == 3:
            return f"success!"

    with click.progressbar([1, 2, 3], label="updating scriptor...", item_show_func=step_label) as bar:
        for element in bar:
            match element:
                case 1:
                    urlretrieve(download_url, tmp_zip_file)
                case 2:
                    with zipfile.ZipFile(tmp_zip_file) as zip_f:
                        zip_f.extractall(scriptor_path)
                case 3:
                    tmp_zip_file.unlink()
                    bar.label = "updated successful"
