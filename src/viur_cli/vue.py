import click, os, shutil, json
from . import cli, echo_error, get_config, write_config


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(['add', 'remove', 'build', 'serve']))
@click.argument("additional_args", nargs=-1)
def vue(action, additional_args):
    """build gulp assets"""

    additional_args = list(additional_args)

    if action == "add":
        vue_add(additional_args)
    elif action == "remove":
        vue_remove(additional_args)
    elif action == "build":
        vue_build(additional_args)
    elif action == "serve":
        vue_serve(additional_args)


def vue_add(additional_args):
    """add a vue app to project.json"""
    projectConfig = get_config()
    if "default" not in projectConfig:
        raise click.ClickException(click.style("default entry is missing", fg="red"))

    if not "vue" in projectConfig["default"]:
        projectConfig["default"].update({"vue": {}})

    projectConfig["default"]["vue"].update({
        click.prompt('name'): {
            "source": click.prompt('source')
        }
    })

    write_config(projectConfig)


def vue_remove(additional_args):
    """remove a vue app from project.json"""
    projectConfig = get_config()
    if "default" not in projectConfig:
        raise click.ClickException(click.style("default entry is missing", fg="red"))

    if not "vue" in projectConfig["default"]:
        raise click.ClickException(click.style("there are no vue apps in project.json", fg="red"))

    if additional_args[0] not in projectConfig["default"]["vue"]:
        raise click.ClickException(
            click.style(f"app with name '{additional_args[0]}' does not exist in project.json", fg="red"))

    del projectConfig["default"]["vue"][additional_args[0]]

    write_config(projectConfig)


def vue_build(additional_args):
    projectConfig = get_config()
    try:
        if len(additional_args) == 0:
            app_entry = projectConfig['default']['vue'][list(projectConfig["default"]["vue"].keys())[0]]
        else:
            app_entry = projectConfig['default']['vue'][additional_args[0]]
    except:
        app_entry = None

    if not app_entry:
        echo_error("no vue app found")
        return 0

    os.system(f'cd {app_entry["source"]} && npm run build')


def vue_serve(additional_args):
    projectConfig = get_config()
    try:
        if len(additional_args) == 0:
            app_entry = projectConfig['default']['vue'][list(projectConfig["default"]["vue"].keys())[0]]
        else:
            app_entry = projectConfig['default']['vue'][additional_args[0]]
    except:
        app_entry = None

    if not app_entry:
        echo_error("no vue app found")
        return 0

    os.system(f'cd {app_entry["source"]} && npm run serve')
