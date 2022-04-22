import click, os, json, sys
from . import cli, echo_error, get_config, echo_info


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(['app', 'index', 'cron', 'queue']))
@click.argument("name", default='develop')
@click.argument("additional_args", nargs=-1)
def deploy(action, name, additional_args):
    """deploy gcloud app or different yaml files"""
    projectConfig = get_config()

    if name not in projectConfig:
        echo_error(f"{name} is not a valid config name.")
        return

    conf = projectConfig["default"].copy()
    conf.update(projectConfig[name])

    if action == "app":
        # rebuild requirements.txt
        create_req()

        os.system(
            f'gcloud app deploy --project={conf["application_name"]} --version={conf["version"]} --no-promote {" ".join(additional_args)} {conf["distribution_folder"]}')
    else:
        if action not in ["index", "queue", "cron"]:
            echo_error(f"{action} is not a valid action. Valid is app, index, queue, cron")

        os.system(
            f'gcloud app deploy --project={conf["application_name"]} {" ".join(additional_args)} {conf["distribution_folder"]}/{action}.yaml')


def create_req():
    """
    load projects pipenv and build a requirements.txt

    cores requirements.txt cant be validated currently, because of the core does not provide a feature for that
    """
    projectConfig = get_config()
    distFolder = projectConfig["default"]["distribution_folder"]
    if projectConfig["default"]["core"] != "submodule":

        if click.confirm(f"Do you want to regenerate the requirements.txt located in the {distFolder}?"):
            os.system(f"pipfile2req  --hashes > {distFolder}/requirements.txt")
            #append setupTools for GCP
            file_object = open(f"{distFolder}/requirements.txt", 'a')
            file_object.write('\nsetuptools==62.0.0 --hash=sha256:7999cbd87f1b6e1f33bf47efa368b224bed5e27b5ef2c4d46580186cbcb1a86a')
            file_object.close()

            echo_info("requirements.txt successfully generated")

        if check_req(f"{distFolder}/requirements.txt"):
            if not click.confirm(f"There are some depencencie errors, are you sure you want to continue?"):
                sys.exit(0)


def check_req(projects_requirements_path):
    import site
    from pip._internal.req import parse_requirements
    from pip._internal.network.session import PipSession

    def requirements_to_dict(requirements):

        ret = {}
        for requirement in requirements:
            package, version = requirement.requirement.split(";")[0].split("==")
            package = package.split("[")[0]

            requirement.options.update({"version":version.strip()})
            ret.update({package.lower():requirement.options})
        return ret

    core_requirements = os.path.join(site.getsitepackages()[0],"viur","requirements.txt")

    if not os.path.exists(core_requirements):
        echo_info("could now find core package, please update the core to validate the requirements.txt")
        return []

    core_requirements_obj = requirements_to_dict(parse_requirements(core_requirements, session=PipSession()))

    projects_requirements_obj = requirements_to_dict(parse_requirements(projects_requirements_path, session=PipSession()))


    errors = []
    for package,options in core_requirements_obj.items():
        if package not in projects_requirements_obj:
            errors.append(f"missing package: {package} with version {options['version']}")
            continue
        elif options["version"]!=projects_requirements_obj[package]["version"]:
            errors.append(f"version missmatch: expected {options['version']} got {projects_requirements_obj[package]['version']}: {package}")
            continue
        else:
            # package exists, test hash
            project_hashes = projects_requirements_obj[package]["hashes"]["sha256"]
            core_hashes = options["hashes"]["sha256"]

            if not set(core_hashes).issubset(set(project_hashes)):
                errors.append(f"package hash missmatch: {package}")

    for error in errors:
        echo_error(error)

    return errors
