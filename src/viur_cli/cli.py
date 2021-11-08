import click, json, os

projectConfig = None
projectConfigFilePath = "./project.json"

__version__ = "0.5.0"


@click.group(invoke_without_command=True)
@click.option("-v", "--version", is_flag=True)
def cli(version):
    """Info output"""
    if version:
        click.echo(f"ViUR-CLI {__version__}")
        return 0
    click.echo("Welcome to ViUR-CLI")
    loadConfig()


@cli.command()
def init():
    """initialize project.json"""
    projectConfig = getConfig()
    try:
        f = open(projectConfigFilePath)
        if click.confirm("project.json already exists, do you want to delete it?"):
            os.remove(projectConfigFilePath)
    except:

        if not projectConfig:
            if click.confirm("Do you want to create a new project.json file?"):
                createNewConfig()


@cli.command()
@click.argument("action", type=click.Choice(['add', 'remove', "info", "addFlare"]))
def config(action):
    """manage project.json and generate if missing"""
    projectConfig = getConfig()
    if action == "add":
        addToConfig()
    elif action == "addFlare":
        _projectconf = addToFlareConfig(projectConfig)
        writeConfig(_projectconf)
    elif action == "remove":
        removeFromConfig()
    elif action == "info":
        click.echo(click.style(json.dumps(projectConfig, indent=4, sort_keys=True), fg="cyan"))


@cli.command()
def create():
    """create a new viur project, > in addition it runs config, flare config and check"""


# functions

def createNewConfig():
    """create new config with project.json default template"""
    _projectconf = {
        "default": {
            "distribution_folder": click.prompt('distribution folder', default="./deploy"),
            "sources_folder": click.prompt('sources folder', default="./sources"),
            "flare": {}
        },

        "develop": {
            "application_name": click.prompt('application name'),
            "version": click.prompt('develop version name')
        }
    }

    if click.confirm("Do you want to configure a flare application?"):
        _projectconf = addToFlareConfig(_projectconf)

    writeConfig(_projectconf)


def loadConfig():
    """load project.json and write to global projetConfig"""
    global projectConfig

    try:
        f = open(projectConfigFilePath, "r")
        projectConfig = json.loads(f.read())
    except:
        echoError("no project.json found")

    return projectConfig


def writeConfig(conf):
    """write current projectConfig dict to project.json"""
    global projectConfig

    projectConfig = conf

    f = open(projectConfigFilePath, "w")
    f.write(json.dumps(conf, indent=4, sort_keys=True))
    f.close()


def getConfig():
    global projectConfig
    return projectConfig


def addToConfig():
    """add a new config to project.json"""
    global projectConfig
    if not projectConfig:
        return

    projectConfig.update({click.prompt('name'): {
        "application_name": click.prompt('application name'),
        "version": click.prompt('develop version name')
    }})

    writeConfig(projectConfig)


def removeFromConfig():
    """remove a config from project.json"""
    global projectConfig
    configname = click.prompt('name')
    try:
        del projectConfig[configname]
        writeConfig(projectConfig)
    except:
        raise click.ClickException(click.style(f"{configname} not found", fg="red"))


def addToFlareConfig(projectconf):
    """add a new flare app to project.json"""
    if "default" not in projectconf:
        raise click.ClickException(click.style("default entry is missing", fg="red"))

    if not "flare" in projectconf["default"]:
        projectconf["default"].update({"flare": {}})

    projectconf["default"]["flare"].update({
        click.prompt('name'): {
            "source": click.prompt('source'),
            "target": click.prompt('target')
        }
    })

    return projectconf


def removeFromFlareConfig(flareAppName):
    """remove a flare app from project.json"""
    global projectConfig
    try:
        del projectConfig["default"]["flare"][flareAppName]
        writeConfig(projectConfig)
    except:
        raise click.ClickException(click.style(f"{flareAppName} not found", fg="red"))


def echoError(msg):
    """colored cli feedback"""
    click.echo(click.style(msg, fg="red"))


def echoInfo(msg):
    """colored cli feedback"""
    click.echo(click.style(msg, fg="cyan"))
