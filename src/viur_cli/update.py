import click
import os
import sys
import re
from .conf import config
from . import cli, echo_error, echo_positive, echo_info, utils


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["requirements"]))
@click.argument("profile", default='default')
@click.argument("additional_args", nargs=-1)
def update(action, profile, additional_args):
    """
    Update project-specific files and dependencies.

    This command allows you to update project-specific files and dependencies for a specified project configuration.
    Currently, it supports the 'requirements' action, which is used to update the requirements.
    The `update` command performs the specified 'action' to update project-specific files or dependencies. It ensures
    that the specified project configuration exists.

    Note:

        - Ensure that the specified project configuration ('name') is valid and defined in your project's configuration.

        - Additional arguments can be used to customize the update process if supported by the action.

    """
    conf = config.get_profile(profile)

    if action == "requirements":
        create_req(True, profile)




def create_req(yes, profile, confirm_value=True):
    """
    Load project's pipenv and build a requirements.txt.

    This function generates a requirements.txt file based on the project's pipenv environment. It offers the option
    to confirm the regeneration of the requirements.txt file.

    :param confirm_value: bool, default: True
        If True, confirms the regeneration of requirements.txt.

    Note:
    - The function handles requirements.txt generation and checking.
    - It prompts for confirmation to regenerate the requirements.txt file.
    - If errors are detected, it provides an option to continue or exit the script.

    :return: None
    """
    conf = config.get_profile(profile)
    dist_folder = conf["distribution_folder"]
    if conf["core"] != "submodule":
        if yes or click.confirm(
                text=f"Do you want to regenerate the requirements.txt located in the {dist_folder}?",
                default=confirm_value):
            os.system(f"pipfile2req  --hashes > {dist_folder}/requirements.txt")
            file_object = open(f"{dist_folder}/requirements.txt", 'r')
            generated_requirements = file_object.read()
            for line in generated_requirements.splitlines():
                if "]==" in line:
                    # we got a dependency with extras
                    generated_requirements += re.sub(r"\[.*?\]", "", line) + "\n"
            file_object.close()

            file_obj = open(f"{dist_folder}/requirements.txt", 'w')
            file_obj.write(generated_requirements)
            file_obj.close()
            echo_info("requirements.txt successfully generated")

        if check_req(f"{dist_folder}/requirements.txt"):
            if not click.confirm(f"There are some depencency errors, are you sure you want to continue?"):
                sys.exit(0)


def check_req(projects_requirements_path):
    """
    Check project's requirements against core requirements.

    This function checks the project's requirements to validate package versions and hashes.
    It identifies and reports errors if there are discrepancies.

    :param projects_requirements_path: str
        The path to the project's requirements.txt file.

    :return: list
        A list of error messages, if any, indicating package version and hash discrepancies.
    """
    import site
    from pip._internal.req import parse_requirements
    from pip._internal.network.session import PipSession

    sp = site.getsitepackages()[0]
    core_requirements = None
    for req in (
            os.path.join(sp, "viur", "core", "requirements.txt"),
            os.path.join(sp, "viur", "requirements.txt")
    ):
        if os.path.exists(req):
            core_requirements = req
            break

    if not core_requirements:
        echo_error("could now find core package, please update the core to validate the requirements.txt")

    core_requirements_obj = utils.requirements_to_dict(parse_requirements(core_requirements, session=PipSession()))

    projects_requirements_obj = utils.requirements_to_dict(
        parse_requirements(projects_requirements_path, session=PipSession())
    )

    errors = []
    for package, options in core_requirements_obj.items():
        if package not in projects_requirements_obj:
            errors.append(f"missing package: {package} with version {options['version']}")
            continue
        elif options["version"] != projects_requirements_obj[package]["version"]:
            errors.append(
                f"version mismatch: expected {options['version']} "
                f"got {projects_requirements_obj[package]['version']}: {package}"
            )
            continue
        else:
            # package exists, test hash
            project_hashes = projects_requirements_obj[package]["hashes"]["sha256"]
            core_hashes = options["hashes"]["sha256"]

            if not set(core_hashes).issubset(set(project_hashes)):
                errors.append(f"package hash mismatch: {package}")

    for error in errors:
        echo_error(error)

    return errors
