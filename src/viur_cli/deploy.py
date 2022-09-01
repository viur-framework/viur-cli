import click, os, string, sys, re, yaml
from . import cli, echo_error, get_config, echo_info, replace_vars


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
        version = replace_vars(
            conf["version"],
            {k: v for k, v in conf.items() if k not in ["version"]}
        )

        # gcloud only allows for version identifiers in lower-case order and only accepting these characters
        version = "".join([c for c in version.lower() if c in string.ascii_lowercase + string.digits + "-"])

        # rebuild requirements.txt
        create_req()

        os.system(
            f'gcloud app deploy --project={conf["application_name"]} --version={version} --no-promote {" ".join(additional_args)} {conf["distribution_folder"]}')
    else:
        if action not in ["index", "queue", "cron"]:
            echo_error(f"{action} is not a valid action. Valid is app, index, queue, cron")

        yaml_file = f'{conf["distribution_folder"]}/{action}.yaml'

        # Sort index.yaml by kind name, making it more clean to view.
        if action == "index":
            try:
                with open(yaml_file, "r") as source_file:
                    try:
                        data = yaml.safe_load(source_file)
                    except:
                        raise ValueError()

                    if "indexes" not in data:
                        raise ValueError()

                    indexes = sorted(
                        data["indexes"],
                        key=lambda k: k["kind"] if isinstance(k, dict) and "kind" in k else k
                    )

                    # Only update index.yaml when something has changed
                    if data["indexes"] != indexes:
                        data["indexes"] = indexes

                        with open(yaml_file, "a+") as dst_file:
                            dst_file.seek(0)
                            dst_file.truncate()
                            dst_file.write(
                                yaml.dump(data).replace("- kind: ", "\n- kind: ")
                            )

                        echo_info(f"{yaml_file} has been sorted by kind")

            except FileNotFoundError:
                echo_error(f"{yaml_file} not found")
                return
            except ValueError:
                echo_error(f"{yaml_file} is not a valid")
                return

        os.system(
            f'gcloud app deploy --project={conf["application_name"]} {" ".join(additional_args)} {yaml_file}')

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

            file_object = open(f"{distFolder}/requirements.txt", 'r')
            generated_requirements = file_object.read()
            for line in generated_requirements.splitlines():
                if "]==" in line:
                    # we got a dependency with extras
                    generated_requirements+=re.sub(r"\[.*?\]","",line)+"\n"
            file_object.close()

            file_obj = open(f"{distFolder}/requirements.txt", 'w')
            file_obj.write(generated_requirements)
            file_obj.close()
            echo_info("requirements.txt successfully generated")

        if check_req(f"{distFolder}/requirements.txt"):
            if not click.confirm(f"There are some depencency errors, are you sure you want to continue?"):
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
            errors.append(f"version mismatch: expected {options['version']} got {projects_requirements_obj[package]['version']}: {package}")
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
