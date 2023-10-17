import click
import os
import sys
import re
from . import cli, echo_error, get_config, echo_info, utils


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["requirements"]))
@click.argument("name", default='develop')
@click.argument("additional_args", nargs=-1)
def update(action, name, additional_args):
    """update project specific files and dependencies"""
    project_config = get_config()

    if name not in project_config:
        echo_error(f"{name} is not a valid config name.")
        return

    if action == "requirements":
        create_req()


def create_req(confirm_value=True):
    """
    load projects pipenv and build a requirements.txt

    cores requirements.txt cant be validated currently, because of the core does not provide a feature for that
    """
    project_config = get_config()
    dist_folder = project_config["default"]["distribution_folder"]
    if project_config["default"]["core"] != "submodule":

        if click.confirm(text="Do you want to regenerate the requirements.txt located in the {dist_folder}?",
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
