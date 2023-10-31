import click
import os
import string
import yaml
from . import cli, echo_error, get_config, echo_info, replace_vars
from .update import create_req


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(['app', 'index', 'cron', 'queue']))
@click.argument("name", default='develop')
@click.argument("additional_args", nargs=-1)
def deploy(action, name, additional_args):
    """
    Deploy a Google Cloud application or different YAML files.

    This command allows you to deploy various components of a Google Cloud application, such as the app itself, index.yaml
    configurations, cron.yaml configurations, or queue.yaml configurations. The deployment action and the specific
    project configuration to deploy are determined by the 'action' and 'name' parameters.
    Please make sure to configure your global installation of the gcloud-cli accordingly.

    :param action: str
        The deployment action. It can be one of the following:
        - 'app': Deploy the Google Cloud application.
        - 'index': Deploy the index.yaml configuration.
        - 'cron': Deploy the cron.yaml configuration.
        - 'queue': Deploy the queue.yaml configuration.

    :param name: str, default: 'develop'
        The name of the project configuration to use for deployment. It should correspond to a valid project configuration.

    :param additional_args: tuple
        Additional arguments that can be passed to the deployment process.

    Example Usage:
    ```shell
    viur deploy app my_config --version v2
    viur deploy index my_config
    viur deploy cron my_config
    viur deploy queue my_config
    ```

    The `deploy` command deploys the specified components based on the 'action' and 'name' parameters. It includes checks
    for successful deployments and offers a confirmation prompt for any failed checks.

    Note:
    - Ensure that the specified project configuration ('name') is valid and defined in your project's configuration.
    - The 'app' action includes vulnerability checks and a confirmation prompt if checks fail.
    - The 'index' action sorts the index.yaml file by kind for cleaner organization.

    :return: None
    """
    projectConfig = get_config()

    if name not in projectConfig:
        echo_error(f"{name} is not a valid config name.")
        return

    conf = projectConfig["default"].copy()
    conf.update(projectConfig[name])

    if action == "app":
        from . import do_checks
        if not do_checks(dev=False):
            if not click.confirm(f"The checks were not successful, do you want to continue?"):
                return
        else:
            echo_info("\U00002714 No vulnerabilities found.")
        version = replace_vars(
            conf["version"],
            {k: v for k, v in conf.items() if k not in ["version"]}
        )

        # gcloud only allows for version identifiers in lower-case order and only accepting these characters
        version = "".join([c for c in version.lower() if c in string.ascii_lowercase + string.digits + "-"])

        # rebuild requirements.txt
        create_req(False)

        os.system(
            f'gcloud app deploy --project={conf["application_name"]} --version={version} '
            f'--no-promote {" ".join(additional_args)} {conf["distribution_folder"]}')
    else:
        if action not in ["index", "queue", "cron"]:
            echo_error(f"{action} is not a valid action. Valid is app, index, queue, cron")

        yaml_file = f'{conf["distribution_folder"]}/{action}.yaml'

        # Sort index.yaml by kind name, making it more clean to view.
        if action == "index":
            try:
                with open(yaml_file, "r") as source_file:
                    data = yaml.safe_load(source_file)

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
