import click, os, zipfile, shutil
from . import cli, echoError, getConfig
from urllib.request import urlretrieve


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("version", default="latest")
def vi(version):
    """download latest vi or a specific version"""
    projectConfig = getConfig()
    distFolder = projectConfig["default"]["distribution_folder"]

    viRepo = "https://github.com/viur-framework/viur-vi"
    viPath = os.path.join(distFolder, "vi")
    tempZipFile = "./vi.zip"

    if version == "latest":
        vibaseUrl = f"{viRepo}/releases/latest/download/viur-vi.zip"
    else:
        vibaseUrl = f"{viRepo}/releases/download/v{version}/viur-vi.zip"

    click.echo(f"downloading {version} vi...")
    urlretrieve(vibaseUrl, tempZipFile)

    if os.path.exists(viPath):
        click.echo(f"remove old vi...")
        shutil.rmtree(viPath)

    click.echo(f"extracting new vi...")
    with zipfile.ZipFile(tempZipFile) as zip_f:
        zip_f.extractall(viPath)

    os.remove(tempZipFile)
    click.echo(f"success!")
