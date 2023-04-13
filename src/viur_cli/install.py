import click, os, zipfile, shutil, urllib, json
from . import cli, get_config, echo_error, write_config
from urllib.request import urlretrieve


@cli.group()
def install():
    """Install VIUR features"""

@install.command()
@click.argument("version", default="latest")
@click.option('--next', '-n', 'next_',  is_flag=True, default=False)
@click.option('--target', '-t',  default="vi")
def vi(version, target, next_):
    """Install VI administration interface."""

    if next_:
        downloadnextvi()
        return 0

    """download latest vi or a specific version"""
    projectConfig = get_config()
    distFolder = projectConfig["default"]["distribution_folder"]

    viRepo = "https://github.com/viur-framework/viur-vi"
    viPath = os.path.join(distFolder, target)

    tempZipFile = "./vi.zip"

    if version == "latest":
        vibaseUrl = f"{viRepo}/releases/latest/download/viur-vi.zip"
    else:
        vibaseUrl = f"{viRepo}/releases/download/v{version}/viur-vi.zip"

    def get_version_info(version):
        url = "https://api.github.com/repos/viur-framework/viur-vi/releases"
        if version == "latest":
            try:
                resp = json.loads(urllib.request.urlopen(url).read().decode("utf-8"))
                projectConfig["default"]["vi"] = resp[0]["name"][1:]
                write_config(projectConfig)
            except:
                echo_error("Error while fetching version info")
        else:
            projectConfig["default"]["vi"] = f'{version}'
            write_config(projectConfig)

    get_version_info(version)

    def step_label(step):
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
                urlretrieve(vibaseUrl, tempZipFile)
            elif element == 2:
                if os.path.exists(viPath):
                    shutil.rmtree(viPath)
            elif element == 3:
                with zipfile.ZipFile(tempZipFile) as zip_f:
                    zip_f.extractall(viPath)
            elif element == 4:
                os.remove(tempZipFile)
                bar.label = "updated successful"


def downloadnextvi():
    """download latest vi or a specific version"""
    projectConfig = get_config()
    distFolder = projectConfig["default"]["distribution_folder"]

    viRepo = "https://github.com/viur-framework/viur-vuevi"
    viPath = os.path.join(distFolder, "vi")
    tempZipFile = "./vi.zip"
    version = "latest"
    vibaseUrl = f"{viRepo}/releases/latest/download/viur-vi.zip"

    def get_version_info(version):
        url = "https://api.github.com/repos/viur-framework/viur-vuevi/releases"
        if version == "latest":
            try:
                resp = json.loads(urllib.request.urlopen(url).read().decode("utf-8"))
                projectConfig["default"]["vi"] = resp[0]["name"]
                write_config(projectConfig)
            except:
                echo_error("Error while fetching version info")
        else:
            projectConfig["default"]["vi"] = f'{version}'
            write_config(projectConfig)

    get_version_info(version)

    def step_label(step):
        if step == 1:
            return f"downloading next vi..."
        elif step == 2:
            return f"remove old vi..."
        elif step == 3:
            return f"extracting new vi..."
        elif step == 4:
            return f"success!"

    with click.progressbar([1, 2, 3, 4], label="updating vi...", item_show_func=step_label) as bar:
        for element in bar:
            if element == 1:
                urlretrieve(vibaseUrl, tempZipFile)
            elif element == 2:
                if os.path.exists(viPath):
                    shutil.rmtree(viPath)
            elif element == 3:
                with zipfile.ZipFile(tempZipFile) as zip_f:
                    zip_f.extractall(viPath)
            elif element == 4:
                os.remove(tempZipFile)
                bar.label = "updated successful"


@install.command()
@click.argument("version", default="latest")
def scriptor(version):
    """Install scriptor IDE."""
    projectConfig = get_config()
    dist_folder = projectConfig["default"]["distribution_folder"]

    scriptor_repo = "https://github.com/viur-framework/viur-scriptor"
    scriptor_path = os.path.join(dist_folder, "scriptor")
    tmp_zip_file = "./scriptor.zip"
    scriptor_base_url = f"{scriptor_repo}/releases/latest/download/source.zip"

    def get_version_info(version):
        url = "https://api.github.com/repos/viur-framework/viur-scriptor/releases"
        if version == "latest":
            try:
                resp = json.loads(urllib.request.urlopen(url).read().decode("utf-8"))
                projectConfig["default"]["scriptor"] = resp[0]["name"]
                write_config(projectConfig)
            except:
                echo_error("Error while fetching version info")
        else:
            projectConfig["default"]["scriptor"] = f'{version}'
            write_config(projectConfig)

    get_version_info(version)

    def step_label(step):
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
                    urlretrieve(scriptor_base_url, tmp_zip_file)
                case 2:
                    zipfile.ZipFile(tmp_zip_file).extractall()
                case 3:
                    os.remove(tmp_zip_file)
                    bar.label = "updated successful"
