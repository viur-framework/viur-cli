import json
from pathlib import Path
import subprocess
import os
import string
import time
import click
import yaml
from viur_cli import echo_positive, echo_warning, echo_fatal
from .conf import config
from . import cli, echo_error, echo_info, replace_vars
from .update import create_req


@cli.group()
def cloud():
    """This method defines a command group for working with cloud resources."""


@cloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["bucket2bucket", "bucket2local", "local2bucket"]))
@click.argument("profile", default="default")
def copy(action, profile):
    if action == "bucket2bucket":
        if user_check_login():
            storage_copy()

    if action == "bucket2local":
        if user_check_login():
            datastore_import(profile)

    if action == "local2bucket":
        if user_check_login():
            datastore_export(profile)


def user_check_login():
    return click.confirm("Are you logged in with your gcloud admin account?", default=False, show_default=True)


def storage_copy():
    # https://console.cloud.google.com/transfer/jobs
    source = click.prompt('Source bucketname')
    target = click.prompt('Target bucketname')
    if not click.confirm(text=f"Copy from {source} to {target}", default=True):
        print("Abort ...")
        return 0
    print(f"gsutil -m cp -r gs://{source}/ gs://{target}/")
    os.system(f"gsutil -m cp -r gs://{source} gs://{target}")


def datastore_import(profile):
    conf = config.get_profile(profile)
    target = click.prompt('path to overall_export_metadata')
    os.system(f"gcloud datastore import gs://{target} --project={conf['application_name']}")


def datastore_export(profile):
    conf = config.get_profile(profile)
    target = click.prompt('bucketname')
    timestamp = f'{datetime.now().strftime("%Y%m%d-%H%M%S")}-manual'
    format = "default"
    os.system(
        f"gcloud datastore export gs://{target}/{timestamp}-{format} --format={format} --project={conf['application_name']} ")


@cloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["backup"]))
def enable(action):
    """Enable a specific action based on the provided parameter."""
    if action == "backup":
        enable_gcp_backup()


def enable_gcp_backup():
    """
    Enables Google Cloud Platform backups for the project.

    This method performs the following steps:
    1. Loads the project configuration using the "default" profile.
    2. Creates helper variables for the project ID and the backup bucket name.
    3. Constructs the command to create the backup bucket using gsutil.
    4. Executes the command to create the backup bucket.
    5. If the bucket creation fails, it prints an error message.
    6. Creates helper variables for the IAM roles and the service worker email.
    7. Adds the IAM policy bindings for the service worker with the specified roles.
    8. If an error occurs during the role binding, it prints an error message.
    9. Prints a success message.

    Note:
    - The backup bucket is created in the europe-west3 region.
    - The IAM roles "roles/storage.admin" and "roles/datastore.importExportAdmin" are used.

    :return: None
    """
    # Load the project Config
    conf = config.get_profile("default")

    # Create helper Variables
    project_id = conf["application_name"]
    bucket_name = f'backup-dot-{project_id}'
    backup_bucket_command = f'gsutil mb -l EUROPE-WEST3 -p {project_id} gs://{bucket_name}'

    # Create the Backup Bucket
    try:
        result = subprocess.run(
            backup_bucket_command,
            capture_output=True,
            shell=True,
        )
        if result.returncode != 0:
            echo_error('Error creating bucket.')

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


@cloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("service", type=click.Choice(["gcloud"]), default="gcloud")
@click.argument("profile", default="default")
def init(service, profile):
    """
    Initializes the cloud service deployment.

    Parameters:
        - service (str): The cloud service to be initialized. Expected values are 'gcloud'.
        - profile (str): The profile name to be used for initialization. Default value is 'default'.

    """
    deployments = ["cron", "queue", "cron"]
    if service == "gcloud":
        for element in deployments:
            os.system(f"viur cloud deploy {element} {profile} -y")


@cloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("service", type=click.Choice(["gcloud"]), default="gcloud")
@click.argument("option", type=click.Choice(["datastore"]), default="datastore")
@click.argument("profile", default="default")
def cleanup(service, option, profile):
    """
    Cleans up the indexes in the specified service and option.

    Parameters:
    - service (str): The service to clean up the indexes for.
    - option (str): The option to clean up the indexes for.
    - profile (str): The profile to use for configuration.

    """
    conf = config.get_profile(profile)

    if service == "gcloud" and option == "datastore":
        run_command(f"gcloud datastore indexes cleanup deploy/index.yaml --project={conf['application_name']}")


@cloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["backup"]))
def disable(action):
    """Disables a specific action."""
    if action == "backup":
        disable_gcp_backup()


def disable_gcp_backup():
    """
    Disables Google Cloud Platform(GCP) backups for a specified project.

    This method disables GCP backups by performing the following steps:
    1. Loads the project configuration from the "default" profile.
    2. Creates helper variables for the project ID and backup bucket name.
    3. Removes the backup bucket by executing the appropriate command using gsutil.
    4. If an error occurs during bucket removal, an error message is printed.
    5. Creates helper variables for the IAM roles and service worker email.
    6. Removes the IAM policy bindings for the specified roles using the gcloud command.
    7. If an error occurs during roles removal, an error message is printed.
    8. Prints a success message if all steps complete successfully.

    Returns:
        None

    Raises:
        Any exception that occurs during the execution of the method.

    Note:
        - Make sure to have the correct Google Cloud Access rights.
    """

    # Load the project Config
    conf = config.get_profile("default")

    # Create helper Variables
    project_id = conf["application_name"]
    bucket_name = f'backup-dot-{project_id}'
    backup_bucket_command = f'gsutil rm -r gs://{bucket_name}'

    # Remove the Backup Bucket
    try:
        result = subprocess.run(
            backup_bucket_command,
            capture_output=True,
            shell=True,
        )
        print(result)
        if result.returncode != 0:
            print('Error removing bucket.')

    except Exception as e:
        print(f'An Error Occured:\n {e} Please make sure you have the correct Google Cloud Access rights')

    # Helper Variables for IAM
    iam_roles = ["roles/storage.admin", "roles/datastore.importExportAdmin"]
    service_worker_mail = f'{project_id}@appspot.gserviceaccount.com'

    for r in iam_roles:
        iam_roles_command = (f'gcloud projects remove-iam-policy-binding {project_id} --member '
                             f'serviceAccount:{service_worker_mail} --role {r}')
        try:
            subprocess.run(iam_roles_command, capture_output=True, shell=True)

        except Exception as e:
            print(f'An Error Occured during Roles {e}\n '
                  f'Please make sure you have the correct Google Cloud Access rights'
                  )
            return

    echo_info('Success! Gcloud Backups have been disabled')


@cloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["gcroles"]))
@click.argument("profile", default="default")
def setup(action, profile):
    """
    Set up the specified action for the given profile.
    """
    if action == "gcloud":
        if os.path.exists('deploy'):
            gcloud_setup()
        else:
            echo_error("No 'deploy' directory found in your current working directory."
                       "\n Please make sure you are in the correct directory."
                       "\n If you want to create a new ViUR Project use 'viur create {name}'")
    if action == "gcroles":
        gcloud_setup_roles(profile)


@cloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["gcroles"]))
@click.argument("profile", default='default')
def get(action, profile):
    """Get Method to retrieve Information from Cloud Service Environment"""

    if action == "gcroles":
        gcloud_get_roles(profile)


def gcloud_get_roles(profile):
    """
    Retrieve IAM roles from Google Cloud Platform using the gcloud command-line tool.

    :param profile: String:
        The profile name to use for retrieving the roles.

    :raises:
        subprocess.CalledProcessError: If an error occurs while fetching the role data.

    Note:
    - This method requires the gcloud command-line tool to be installed and configured in the environment.
    - The gcloud configuration file should contain the necessary authentication information.

    """
    conf = config.get_profile(profile)

    try:
        # Run gcloud command to get IAM policy and save it to a YAML file
        yaml_file_path = f"./{conf['application_name']}.yaml"
        run_command(f"gcloud projects get-iam-policy {conf['application_name']} > {yaml_file_path}")

        try:
            # Load YAML data and transform it to a dictionary
            with open(yaml_file_path, "r") as file:
                roles_dict = yaml.safe_load(file)
                usable_dict = transform_yaml_to_dict(roles_dict)

                # Save the transformed dictionary to a JSON file
                json_file_path = f"./{profile}_roles.json"
                with open(json_file_path, 'w') as json_file:
                    json.dump(usable_dict, json_file, indent=4)

                echo_positive(f"You can now watch your gcloud Roles Setup in your '{json_file_path}' file ")

        except yaml.YAMLError as e:
            echo_error(f"An error occurred during YAML to Dictionary transformation: {e}")

        finally:
            # Delete the temporary YAML file
            if os.path.exists(yaml_file_path):
                os.remove(yaml_file_path)

    except subprocess.CalledProcessError:
        echo_error("An error occurred while fetching Role data")


def gcloud_setup_roles(profile):
    """
    Sets up roles in Google Cloud Platform (GCP) based on the given profile.

    :param profile: The profile to use for setting up roles in GCP
    :type profile: str

    :raises json.JSONDecodeError: If there is an error decoding JSON from the roles JSON file
    :raises yaml.YAMLError: If there is an error opening or writing the .yaml file

    """
    conf = config.get_profile(profile)

    # Use a more descriptive variable name for the JSON file
    roles_json_file_path = f"{profile}_roles.json"

    try:
        with open(roles_json_file_path, "r") as json_file:
            # Load roles from the JSON file and transform to .yaml
            roles = json.load(json_file)
            yaml_data = transform_dict_to_yaml(roles)
            yaml_file_path = f"./{conf['application_name']}.yaml"

            # Save YAML data to a file
            with open(yaml_file_path, 'w') as yaml_file:
                yaml.dump(yaml_data, yaml_file, default_flow_style=False)

                try:
                    # Run gcloud command to get IAM policy
                    run_command(f"gcloud projects get-iam-policy {conf['application_name']} {yaml_file_path}")
                except ValueError as e:
                    echo_error(f"An error occurred while uploading Role data to Cloud: {e}")

    except json.JSONDecodeError as e:
        echo_fatal(f"Error decoding JSON from {roles_json_file_path}: {e}")
    except yaml.YAMLError as e:
        echo_fatal(f"Error opening or writing the .yaml file: {e}")


def transform_yaml_to_dict(dict_data):
    """
    Transforms a YAML file to a dict Object
    """
    transformed_data = {'bindings': []}

    # Create a dictionary to store unique members and their corresponding roles
    member_roles = {}

    # Iterate through the original data and organize it
    for binding in dict_data['bindings']:
        role = binding['role']
        for member in binding['members']:
            member_roles.setdefault(member, []).append(role)

    # Create the transformed data structure
    transformed_data['bindings'] = [{'members': member, 'role': roles} for member, roles in member_roles.items()]

    # Add E-Tag and Version
    transformed_data.update({"etag": dict_data["etag"], "version": dict_data["version"]})

    return transformed_data


def transform_dict_to_yaml(transformed_data):
    """
    Transforms a dictionary to YAML format.

    :param transformed_data: Dictionary
        The transformed data in dictionary format.

    :returns: dict
        The original data in YAML format.
    """
    original_data = {'bindings': []}

    # Create a dictionary to store roles and their corresponding members
    role_members = {}

    # Iterate through the transformed data and organize it
    for binding in transformed_data['bindings']:
        members = binding['members']
        roles = binding['role']

        # Ensure members is a list
        members = [members] if not isinstance(members, list) else members

        for role in roles:
            role_members.setdefault(role, []).extend(members)

    # Create the original data structure
    original_data['bindings'] = [
        {'members': list(set(members)), 'role': role} for role, members in role_members.items()
    ]

    # Add E-Tag and Version
    original_data.update({"etag": transformed_data["etag"], "version": transformed_data["version"]})

    return original_data


# Helper function for running Commands in subprocess and getting the Output
def run_command(command):
    """
    Executes the specified command in the system shell and returns the output.

    :param command: String
        The command to be executed in the Subprocess.
    """
    try:
        return subprocess.check_output(command, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")


@cloud.command()
@click.argument("action", type=click.Choice(['app', 'index', 'cron', 'queue', 'cloudfunction']))
@click.argument("profile", default='default')
@click.argument("additional_args", nargs=-1)
@click.option("--ext", "-e", default=None)
@click.option("--yes", "-y", is_flag=True, default=False)
@click.option("--skip_checks", is_flag=True, help="Skip the security checks before the deployment")
@click.option("--name", "-n", default=None)
def deploy(action, profile, name, ext, yes, skip_checks: bool, additional_args):
    """Deploy the specified action to a cloud"""

    conf = config.get_profile(profile)

    if action == "app":
        if not skip_checks:
            from . import do_checks
            if not do_checks(dev=False):
                # --yes will not be implemented here because deploying security issues should be an explicit decission
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

        if ext:
            version += f"-{ext}"

        # rebuild requirements.txt
        create_req(yes, profile, confirm_value=False)

        app_yaml = Path(conf["distribution_folder"]) / conf.get("appyaml", "app.yaml")
        app_yaml_tmp = app_yaml_hidden = None
        if appyaml_substitition := conf.get("appyaml_substitition"):
            app_yaml_tmp = app_yaml.with_stem(f"app{time.time_ns()}.tmp")

            susbtitutions = {
                "$PROJECT_ID": conf["application_name"],
                "$PROJECT_VERSION": version,
                "$CLI_PROFILE": profile,
            }
            if isinstance(appyaml_substitition, dict):
                susbtitutions |= appyaml_substitition

            new_content = app_yaml.read_text()
            for pattern, replacment in susbtitutions.items():
                new_content = new_content.replace(pattern, replacment)
            app_yaml_tmp.write_text(new_content)
            additional_args = [f"--appyaml={app_yaml_tmp.resolve()}", *additional_args]

            # Sadly the --appyaml does only work if the deploy dir does not contain an app.yaml,
            # thefore we make it "hidden" for the gcloud CLI if there is "app.yaml" is not
            # named differently
            if app_yaml.name == "app.yaml":
                app_yaml_hidden = app_yaml.with_stem(f".{app_yaml.stem}")
                app_yaml.rename(app_yaml_hidden)

        elif app_yaml.name != "app.yaml":
            # No substitution is used, but an different app.yaml name
            additional_args = [f"--appyaml={app_yaml_tmp.resolve()}", *additional_args]

        try:
            os.system(
                f'gcloud app deploy --project={conf["application_name"]} --version={version} '
                f'--no-promote {" ".join(additional_args)} {conf["distribution_folder"]} {"-q" if yes else ""}'
            )
        finally:
            if app_yaml_tmp is not None:
                app_yaml_tmp.unlink()
            if app_yaml_hidden is not None:
                app_yaml_hidden.rename(app_yaml)

    elif action == "cloudfunction":
        os.system(build_deploy_command(name, conf["gcloud"]))

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
            f'gcloud app deploy --project={conf["application_name"]} {" ".join(additional_args)} {yaml_file} {"-q" if yes else ""}')


def build_deploy_command(name, conf):
    """

    Builds a deployment command for a cloud function.

    :param name: The name of the cloud function to deploy. If not provided, the user will be prompted to enter it.
    :type name: str
    :param conf: The project configuration.
    :type conf: dict
    :return: The deployment command.
    :rtype: str

    The method builds a command for deploying a cloud function using the Google Cloud Platform (GCP) CLI. It first checks if the name of the cloud function is provided. If not, it prompts
    * the user to enter it using the `click.prompt` function. It then checks if the provided name exists in the project configuration.

    The deployment command is built using a formatted string that includes the function name and the specified region. Additionally, the `max-instances` parameter from the project configuration
    * is included in the command.

    Next, the method iterates over the configuration of the specified cloud function and adds additional parameters to the command based on the key-value pairs. If the key is "trigger",
    * "update", "set", or "remove", it adds a flag to the command including the key and its corresponding value. Otherwise, it adds a flag to the command including the key and its corresponding
    * value as a string.

    Finally, the built command is returned.
    """

    if not name:
        name = click.prompt("Please enter the name of the cloudfunction you want to deploy")

    if name not in conf["functions"]:
        echo_fatal(f"The cloudfunction {name} was not found your project.json\n "
                   f"You can create a cloudfunction entry by calling 'viur cloud create function'")

    command = (
        f"gcloud run deploy "
        f"{name} "
        f"--region='{conf['region']}'"
        f"--max-instances={conf['max-instances']}"
    )

    for k, v in conf["functions"][name].items():
        if k == "gen":
            command += f" --{k}{v}"
        elif k in ["trigger", "update", "set", "remove"]:
            command += f"--{k}-{v}"
        else:
            command += f" --{k}='{str(v)}'"

    return command


@cloud.command()
@click.argument("action", type=click.Choice(['function']))
@click.argument("profile", default="default")
@click.option("--gen", "-g")
@click.option("--source", "-src")
@click.option("--name", "-n")
@click.option("--entrypoint", "-ep")
@click.option("--env-vars-file", "-ev")
@click.option("--memory", "-mem")
@click.option("--runtime", "-rt")
@click.option("--trigger", "-tr")
def create(profile, action, gen, source, name, entrypoint, env_vars_file, memory, runtime, trigger):
    """Creates a cloud function based on the provided parameters."""
    if action == "function":
        conf = config.get_profile(profile)
        # First layer initialization:
        conf["gcloud"] = conf.get("gcloud", {})
        conf["gcloud"]["functions"] = conf["gcloud"].get("functions", {})

        conf["gcloud"]["max-instances"] = conf["gcloud"].get("max-instances", click.prompt(
            "Please input the Max Instances your cloud functions should run on", default="1"))

        conf["gcloud"]["region"] = conf["gcloud"].get("region", click.prompt(
            "Please enter your default cloud function region", default="europe-west3"))

        # function layer
        function_name = name if name else click.prompt("Please enter the Name of your cloud function")
        function_dict = conf["gcloud"]["functions"].get(function_name, {})

        function_dict["gen"] = function_dict.get("gen",
                                                 gen if gen else click.prompt(
                                                     "Please enter your cloud function generation",
                                                     default="2")
                                                 )

        function_dict["entry-point"] = function_dict.get("entry-point",
                                                         entrypoint if entrypoint else click.prompt(
                                                             "Please enter your cloud function entrypoint ",
                                                             default="main")
                                                         )

        function_dict["env-vars-file"] = function_dict.get("env-vars-file",
                                                           env_vars_file if env_vars_file else click.prompt(
                                                               "Enter the name of your environment variables file",
                                                               default="env.yaml")
                                                           )

        function_dict["memory"] = function_dict.get("memory",
                                                    memory if memory else click.prompt(
                                                        "Please enter your cloud function memory usage",
                                                        default="512MB")
                                                    )

        function_dict["runtime"] = function_dict.get("runtime",
                                                     runtime if runtime else click.prompt(
                                                         "Please enter your cloud function runtime",
                                                         default="python312")
                                                     )

        function_dict["trigger"] = function_dict.get("trigger",
                                                     trigger if trigger else click.prompt(
                                                         "Please enter your cloud function trigger type",
                                                         default="https")

                                                     )

        function_dict["source"] = function_dict.get("source",
                                                    source if source else click.prompt(
                                                        "Enter the directory of your cloud function"
                                                        "(deploy/cloudfunction/{FileName})")
                                                    )

        conf["gcloud"]["functions"][function_name] = function_dict

        config[profile] = conf
        config.migrate()
        echo_positive("Your cloud function creation was successful, if you want to add more flags, "
                      "add them in your project.json")

