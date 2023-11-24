import os
import string
import click
import yaml
import subprocess
from . import cli, echo_error, get_config, echo_info, replace_vars
from .update import create_req


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(['app', 'index', 'cron', 'queue']))
@click.argument("name", default='develop')
@click.argument("additional_args", nargs=-1)
def deploy(action, name, additional_args):
    """
    Deploy a Google Cloud application or different YAML files.

    This command allows you to deploy various components of a Google Cloud application, such as the app itself,
    index.yaml configurations, cron.yaml configurations, or queue.yaml configurations.
    The deployment action and the specific project configuration
    to deploy are determined by the 'action' and 'name' parameters.
    Please make sure to configure your global installation of the gcloud-cli accordingly.

    :param action: str
        The deployment action. It can be one of the following:
        - 'app': Deploy the Google Cloud application.
        - 'index': Deploy the index.yaml configuration.
        - 'cron': Deploy the cron.yaml configuration.
        - 'queue': Deploy the queue.yaml configuration.

    :param name: str, default: 'develop'
        The name of the project configuration to use for deployment.
        It should correspond to a valid project configuration.

    :param additional_args: tuple
        Additional arguments that can be passed to the deployment process.

    Example Usage:
    ```shell
    viur deploy app my_config --version v2
    viur deploy index my_config
    viur deploy cron my_config
    viur deploy queue my_config
    ```

    The `deploy` command deploys the specified components based on the 'action' and 'name' parameters.
    It includes checks for successful deployments and offers a confirmation prompt for any failed checks.

    Note:
    - Ensure that the specified project configuration ('name') is valid and defined in your project's configuration.
    - The 'app' action includes vulnerability checks and a confirmation prompt if checks fail.
    - The 'index' action sorts the index.yaml file by kind for cleaner organization.

    :return: None
    """
    project_config = get_config()

    if name not in project_config:
        echo_error(f"{name} is not a valid config name.")
        return

    conf = project_config["default"].copy()
    conf.update(project_config[name])

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
                        raise ValueError("indexes section missing in index.yaml")

                    indexes = sorted(
                        data["indexes"],
                        key=lambda k: k["kind"] if isinstance(k, dict) and "kind" in k else k
                    )

                    # Remove duplicate entries with the help of dict,
                    # where keys can only occur once.
                    # The keys are a hashable representation of an entry.
                    indexes = {
                        (
                            entry.get("kind"),
                            tuple(tuple(prop.items())
                                  for prop in entry.get("properties", []))
                        ): entry
                        for entry in indexes
                    }
                    indexes = list(indexes.values())

                    # Only update index.yaml when something has changed
                    if data["indexes"] != indexes:
                        data["indexes"] = indexes

                        with open(yaml_file, "a+") as dst_file:
                            dst_file.seek(0)
                            dst_file.truncate()
                            dst_file.write(
                                yaml.dump(data).replace("- kind: ", "\n- kind: ")
                            )

                        echo_info(f"{yaml_file} has been sorted by kind and duplicates have been removed")

            except FileNotFoundError:
                echo_error(f"{yaml_file} not found")
                return
            except ValueError:
                echo_error(f"{yaml_file} is not a valid")
                return

        os.system(
            f'gcloud app deploy --project={conf["application_name"]} {" ".join(additional_args)} {yaml_file}')


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["backup"]))
def enable(action):
    """
    Enable specific features for the project.

    The 'enable' command allows enabling various features for the project. Currently, only the 'backup' action is
    supported.

    Args:
        action (str): The action to perform. Currently, only 'backup' is supported.

    Example:
    ```bash
    $ viur enable backup
    ```

    """
    if action == "backup":
        enable_gcp_backup()


def enable_gcp_backup():
    # Load the project Config
    project_config = get_config()

    # Create helper Variables
    project_id = project_config["develop"]["application_name"]
    bucket_name = f'backup-dot-{project_id}'
    backup_bucket_command = f'gsutil mb -l EUROPE-WEST3 -p {project_id} gs://{bucket_name}'

    # Create the Backup Bucket
    try:
        result = subprocess.run(
            backup_bucket_command,
            capture_output=True,
            shell=True,
        )
        print(result)
        if result.returncode != 0:
            print('Error creating bucket.')

    except Exception as e:
        print(f'An Error Occured:\n {e} Please make sure you have the correct Google Cloud Access rights')

    # Helper Variables for IAM
    iam_roles = ["roles/storage.admin", "roles/datastore.importExportAdmin"]
    service_worker_mail = f'{project_id}@appspot.gserviceaccount.com'

    for r in iam_roles:
        iam_roles_command = (f'gcloud projects add-iam-policy-binding {project_id} --member '
                             f'serviceAccount:{service_worker_mail} --role {r}')
        try:
            subprocess.run(iam_roles_command, capture_output=True, shell=True)

        except Exception as e:
            print(f'An Error Occured during Roles {e}\n '
                  f'Please make sure you have the correct Google Cloud Access rights'
                  )
            return

    print('Success! It may take a while until you can use Gcloud Backups')
