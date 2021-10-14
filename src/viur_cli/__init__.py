import os, click, json

projectConfig = None
projectConfigFilePath = "./project.json"


def echoError(msg):
    click.echo(click.style(msg, fg="red"))

def echoInfo(msg):
    click.echo(click.style(msg, fg="cyan"))

def loadConfig():
    global projectConfig

    try:
        f = open(projectConfigFilePath, "r")
        projectConfig = json.loads(f.read())
    except:
        echoError("no project.json found")

    return projectConfig

def writeConfig(conf):
    global projectConfig

    projectConfig = conf

    f = open(projectConfigFilePath, "w")
    f.write(json.dumps(conf, indent=4, sort_keys=True))
    f.close()

def addToConfig():
    global projectConfig
    if not projectConfig:
        return

    projectConfig.update({click.prompt('name'): {
        "application_name": click.prompt('application name'),
        "version": click.prompt('develop version name')
    }})

    writeConfig(projectConfig)

def removeFromConfig():
    global projectConfig
    configname = click.prompt('name')
    try:
        del projectConfig[configname]
        writeConfig(projectConfig)
    except:
        raise click.ClickException(click.style(f"{configname} not found", fg="red"))

def addToFlareConfig(projectconf):
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
    global projectConfig
    try:
        del projectConfig["default"]["flare"][flareAppName]
        writeConfig(projectConfig)
    except:
        raise click.ClickException(click.style(f"{flareAppName} not found", fg="red"))

def createNewProject(projectName): pass


def createNewConfig():
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


@click.group(invoke_without_command=True)
def cli():
    """prints info"""
    click.echo("Welcome to ViUR-CLI")
    loadConfig()
    global projectConfig

@cli.command()
def init():
    """initialize project.json"""
    global projectConfig
    try:
        f = open(projectConfigFilePath)
        if click.confirm("project.json already exists, do you want to delete it?"):
            os.remove(projectConfigFilePath)
    except:

        if not projectConfig:
            if click.confirm("Do you want to create a new project.json file?"):
                createNewConfig()

@cli.command()
@click.argument("action", type=click.Choice(['add', 'remove', "info"]))
def config(action):
    """manage project.json and generate if missing"""
    global projectConfig
    if action == "add":
        addToConfig()
    elif action == "remove":
        removeFromConfig()
    elif action == "info":
        click.echo(click.style(json.dumps(projectConfig, indent=4, sort_keys=True), fg="cyan"))

@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("name")
@click.argument("additional_args", nargs=-1)
def deploy(name,additional_args):
    """deploy your application"""
    global projectConfig
    if name not in projectConfig:
        echoError(f"{name} is not a vadid config name.")
        return

    conf = projectConfig["default"].copy()
    conf.update(projectConfig[name])

    os.system(f'gcloud app deploy --project={conf["application_name"]} --version={conf["version"]} --no-promote {" ".join(additional_args)} {conf["distribution_folder"]}')

@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("name")
@click.argument("additional_args", nargs=-1)
def index(name,additional_args):
    """update your application index"""
    global projectConfig
    if name not in projectConfig:
        echoError(f"{name} is not a vadid config name.")
        return

    conf = projectConfig["default"].copy()
    conf.update(projectConfig[name])

    os.system(
        f'gcloud app deploy --project={conf["application_name"]} {" ".join(additional_args)} {conf["distribution_folder"]}/index.yaml')

@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("name", default='develop')
@click.argument("additional_args", nargs=-1)
def run(name, additional_args):
    """start your application locally"""
    global projectConfig
    if name not in projectConfig:
        echoError(f"{name} is not a vadid config name.")
        return

    conf = projectConfig["default"].copy()
    conf.update(projectConfig[name])

    os.system(f'app_server -A={conf["application_name"]} {conf["distribution_folder"]} {" ".join(additional_args)}')

@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("name")
@click.argument("action")
@click.argument("additional_args", nargs=-1)
def flare(action,name,additional_args):
    """build or watch a flare fontend"""
    additional_args = list(additional_args)

    if action =="release":
        additional_args = ["-mzc"]
    elif action =="debug":
        pass
    elif action =="watch":
        additional_args = ["-w"]

    global projectConfig

    if name not in projectConfig["default"]["flare"]:
        echoError(f"{name} is not a vadid flare app name.")
        return

    conf = projectConfig["default"].copy()

    os.system(f'flare -n={name} -s={conf["flare"][name]["source"]} -t={conf["flare"][name]["target"]} {" ".join(additional_args)}')

@cli.command()
def check():
    """check environment"""
    pass

@cli.command()
def create():
    """create a new viur project, > in addition it runs config, flare config and check"""