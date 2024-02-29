"""
Performs build steps configured within the project, or creates any necessary steps for a project deployment build.
"""

import click
import os
from .conf import config
from . import cli, utils


def _build(conf, name, build_cfg, additional_args):
    """
    Internal function to perform steps required for a given build configuration.

    This internal function is responsible for building an application according to the specified build configuration.
    It can handle two types of builds:
        - npm: For building Node.js applications using npm package manager.
        - exec: For executing custom commands specified in the build configuration.

    :param conf: dict
        The project configuration, which can be either the default configuration or project-specific configuration.
    :param name: str
        The name of the application to build.
    :param build_cfg: dict
        The build configuration for the specified application. This configuration includes the "kind" (build type),
        "source" (source folder or path), and "command" (the build command to execute).
    :param additional_args: list
        A list of additional arguments that can be passed to the build process.
    :raises Exception:
        Raises an exception if an unknown build "kind" is encountered in the build configuration.

    The `_build` function performs the following steps based on the build "kind":
    - For "npm" builds, it changes the current directory to the specified source folder, installs npm dependencies, and
    runs the specified npm command.
    - For "exec" builds, it directly executes the specified custom command.

    Note:
    - Ensure that the required dependencies for the specified build type are installed before calling this function.
    - The function is responsible for echoing informative messages during the build process.

    :return: None
    """

    utils.echo_info(f"""- {build_cfg["kind"]} {name}""")
    match build_cfg["kind"]:
        case "npm":
            utils.system(
                " && ".join(
                    (
                        f'cd {os.path.join(conf["sources_folder"], build_cfg["source"])}',
                        "npm install",
                        f'npm run {build_cfg["command"]}'
                    )
                )
            )

        case "exec":
            utils.system(build_cfg["command"])

        case other:
            utils.echo_fatal(f"Unknown build kind {other!r}")


def _clean(conf, name, build_cfg):
    """
    Perform steps required to clean a given build configuration.

    This internal function is responsible for cleaning the artifacts and files generated during the build process
    for a specified application. It supports two types of cleaning methods:
        - npm: For cleaning Node.js applications built with npm package manager.
        - exec: For executing custom clean commands specified in the build configuration.

    :param conf: dict
        The project configuration, which can be either the default configuration or a
        project-specific configuration.

    :param name: str
        The name of the application to clean.

    :param build_cfg: dict
        The build configuration for the specified application. This configuration includes the "kind" (build type),
        "target" (target folder to clean), "source" (source folder or path), "clean" (custom clean command).

    :raises Exception:
        Raises an exception if an unknown build "kind" is encountered in the build configuration.

    The `_clean` function performs the following steps based on the build "kind":
    - For "npm" builds, it deletes the specified target folder, and if available, it executes a custom "clean"
    command.
    - For "exec" builds, it executes the custom clean command provided in the build configuration.

    Note:
    - Ensure that the necessary clean configurations are defined in the build configuration.
    - The function provides informative messages during the cleaning process.

    :return: None
    """

    utils.echo_info(f"""- cleaning {build_cfg["kind"]} {name}""")

    match build_cfg["kind"]:
        # for npm, drop the target folder and node_modules (npm)
        case "npm":
            if target_dir := build_cfg.get("target"):
                target_dir = os.path.join(conf["distribution_folder"], target_dir)
                utils.echo_info(f"  - dropping {target_dir}")
                utils.rmdir(target_dir)

            if build_cfg["kind"] == "npm":
                # todo: Later, call "npm run clean" or a similar command when it exists

                node_modules = os.path.join(conf["sources_folder"], build_cfg["source"], "node_modules")
                utils.echo_info(f"  - dropping {node_modules}")
                utils.rmdir(os.path.join(node_modules))

        case "exec":
            pass

        case other:
            utils.echo_fatal(f"Unknown build kind {other!r}")

    # Always execute explicit "clean" command if provided
    if clean_cmd := build_cfg.get("clean"):
        utils.echo_info(f"  - executing {clean_cmd=}")
        utils.system(clean_cmd)


@cli.group()
def build():
    """Build VIUR project or specific apps."""


@build.command(context_settings={"ignore_unknown_options": True})
@click.argument("profile", default='default')
@click.argument("additional_args", nargs=-1)
def release(profile, additional_args):
    """
    Build all relevant applications to deploy this project.

    This command is used to build all relevant applications necessary for deploying the project. It allows you to
    specify the project configuration to use and any additional arguments to pass to the build process.

    The `release` command loads the specified project configuration, which includes build configurations for
    individual applications. It then iterates through the applications and executes the build process for each one
    using the `_build` function.

    Note:

        - Ensure that the specified project configuration exists.

        - Additional arguments can be used to customize the build process.

    """
    conf = config.get_profile(profile)
    utils.echo_info("building started...")

    for build_name, build_cfg in conf.get("builds", {}).items():
        _build(conf, build_name, build_cfg, additional_args)

    utils.echo_info("building finished!")


@build.command(context_settings={"ignore_unknown_options": True})
@click.argument("appname")
@click.argument("additional_args", nargs=-1)
@click.argument("profile", default="default")
def app(appname, profile, additional_args):
    """
    Build a specific application.

    This function is used to build a specific application as defined in your project's configuration. It allows you to
    specify the name of the application to build and any additional arguments to pass to the build process.

    The `app` function loads the default project configuration, selects the specified application's build configuration,
    and then executes the build process using the `_build` function.

    Note:

        - Ensure that the specified application name is valid and defined in your project's configuration.

        - Additional arguments can be used to customize the build process for this specific application.
    """

    conf = config.get_profile(profile)

    if not (build_cfg := conf.get("builds").get(appname)):
        utils.echo_fatal(f"""{appname=} must be one of these options: {", ".join(conf["builds"].keys())}""")

    utils.echo_info("building started...")
    _build(conf, appname, build_cfg, additional_args)
    utils.echo_info("building finished!")


@build.command
@click.argument("target", default="")
@click.argument("profile", default="default")
def clean(target, profile):
    """
    Clean up build artifacts.

    This command is used to clean up build artifacts and files generated during the build process for one or more
    specific applications. It allows you to specify a target application or clean all applications in the project.

    The `clean` command performs the following actions:

        - If a specific 'target' is provided, it cleans the build artifacts for that application.

        - If 'target' is not provided, it cleans the build artifacts for all applications defined in your project's
        configuration.

    Note:

        - When specifying a 'target,' ensure that it corresponds to a valid application defined in your project.

        - Running the command without a 'target' will clean all applications.
    """

    conf = config.get_profile(profile)

    builds = conf.get("builds", {})
    if target:
        if not (build_cfg := builds.get(target)):
            utils.echo_fatal(f"""{target=} must be one of these options: {", ".join(conf["builds"].keys())}""")

        builds = {target: build_cfg}

    utils.echo_info("clean started...")

    for build_name, build_cfg in builds.items():
        _clean(conf, build_name, build_cfg)

    utils.echo_info("clean finished!")
