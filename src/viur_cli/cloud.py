import json
import subprocess
import os
import string
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
    deployments = ["cron", "queue", "cron"]
    if service == "gcloud":
        for element in deployments:
            os.system(f"viur cloud deploy {element} {profile} -y")

@cloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("service", type=click.Choice(["gcloud"]), default="gcloud")
@click.argument("option", type=click.Choice(["datastore"]), default="datastore")
@click.argument("profile", default="default")
def cleanup(service, option, profile):
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
@click.argument("action", type=click.Choice(["gcloud", "gcroles"]))
@click.argument("profile", default="default")
def setup(action, profile):
    """
    Set up the specified action for the given profile.
    """
    if action == "gcloud":
        gcloud_setup()

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


def gcloud_setup():
    """
    Set up the Google Cloud Platform (GCP) environment for a ViUR project.

    This method performs the following steps:
    1. Prompts the user to enter the GCP project ID.
    2. Checks if the user is authorized with gcloud.
       - If not authorized, prompts the user to authenticate with gcloud and login.
    3. Checks if the GCP App Engine app already exists.
       - If not, prompts the user to create the app and confirm the project is connected to a billing account.
    4. Enables necessary APIs and services for the project.
    5. Configures Google Cloud Storage for the project.
    6. Deploys necessary deployment files (cron.yaml, queue.yaml, index.yaml) to the project.
    7. Checks if the app engine default credentials are set.
       - If not set, prompts the user to authenticate and set the application default user.
    8. Prints a success message with instructions on how to run the project locally.

    Note: This method does not return anything.
    """
    project = input("Enter PROJECT_ID: ").strip()

    if not project:
        echo_fatal("Usage: viur setup gcloud PROJECT_ID")
        return

    echo_info("Check if user is authorized with gcloud....")

    try:
        run_command("gcloud auth print-access-token")
    except subprocess.CalledProcessError:
        echo_warning(
            "##############################################################\n"
            "# Please authenticate your Google user with gcloud SDK to    #\n"
            "# execute administrative commands.                           #\n"
            "# In this step, a separate browser window opens to           #\n"
            "# authenticate.                                              #\n"
            "# This step is only required once on this computer.          #\n"
            "##############################################################\n"
        )
        response = input("Are you ready?[Y/n]")
        if not response.lower() in ("y", ""):
            echo_fatal("User aborted")
            return

        run_command("gcloud auth login --no-ptomote")

    # Check if App already exists
    try:
        run_command(f"gcloud app describe --project={project}")
    except subprocess.CalledProcessError:
        echo_warning(
            "##############################################################\n"
            "# Please check and confirm that your project is created and  #\n"
            "# connected with a billing account in Google Cloud console.  #\n"
            "# Otherwise, some of the following calls may fail.           #\n"
            "##############################################################"
        )
        response = input("Continue? [Y/n] ")
        if not response.lower() in ("y", ""):
            echo_error("User aborted.")
            return

        # Create the Appengine app
        run_command(f"gcloud app create --project={project} --region=europe-west3")

    # Activate APIs and Services
    services = [
        "datastore.googleapis.com",
        "firestore.googleapis.com",
        "iamcredentials.googleapis.com",
        "cloudbuild.googleapis.com",
        "cloudtasks.googleapis.com",
        "cloudscheduler.googleapis.com",
        "secretmanager.googleapis.com"
    ]

    for service in services:
        run_command(f"gcloud services enable --project={project} {service}")

        # Configure Google Cloud Storage
    run_command(f"gsutil uniformbucketlevelaccess set on gs://{project}.appspot.com/")

    for yaml in ["cron.yaml", "queue.yaml", "index.yaml"]:
        run_command(f"cd deploy && gcloud app deploy -q --project={project} {yaml}")

    echo_info("Check if app engine default credentials are set...")
    try:
        run_command("gcloud auth application-default print-access-token")

    except subprocess.CalledProcessError:
        echo_warning(
            "##############################################################\n"
            "# Please authenticate your Google user with gcloud SDK now   #\n"
            "# to set the application default user. This step is required #\n"
            "# to run ViUR applications locally without further           #\n"
            "# credentials that must be supplied from a file.             #\n"
            "# This step is only required once on this computer.          #\n"
            "##############################################################")
        response = input("Are you ready? [Y/n] ")
        if not response.lower() in ("y", ""):
            echo_fatal("User aborted.")
            return

        run_command("gcloud auth application-default login")

    echo_positive(
        "All done!\n"
        "You should now be able to run your project locally with\n"
        "   viur run \n"
        "At the first run, it might happen that some functions are\n"
        "causing error 500 because indexes are not immediately\n"
        "served. Therefore, maybe wait a few minutes.\n"
        "Have a nice day.\n")


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
@click.option("--name", "-n", default=None)
def deploy(action, profile, name, ext, yes, additional_args):
    """ Deploy the specified action to a cloud service."""

    conf = config.get_profile(profile)

    if action == "app":
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

        os.system(
            f'gcloud app deploy --project={conf["application_name"]} --version={version} '
            f'--no-promote {" ".join(additional_args)} {conf["distribution_folder"]} {"-q" if yes else ""}'
        )

    elif action == "cloudfunction":
        os.system(build_deploy_command(name, conf))

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
        f"gcloud functions deploy "
        f"{name} "
        f"--region='{conf['region']}'"
        f"--max-instances={conf['max-instances']}"
    )

    for k, v in conf["functions"][name].items():
        if k in ["trigger", "update", "set", "remove"]:
            command += f"--{k}-{v}"
        else:
            command += f" --{k}='{str(v)}'"

    return command


@cloud.command()
@click.argument("action", type=click.Choice(['function']))
@click.argument("profile", default="default")
@click.option("--source", "-src")
@click.option("--name", "-n", default=None)
@click.option("--entrypoint", "-ep")
@click.option("--env-vars-file", "-ev")
@click.option("--memory", "-mem")
@click.option("--runtime", "-rt")
@click.option("--trigger", "-tr")
def create(profile, action, source, name, entrypoint, env_vars_file, memory, runtime, trigger):
    """Creates a cloud function based on the provided parameters."""
    if action == "function":
        conf = config.get_profile(profile)
        # First layer initialization:
        conf["gcloud"] = conf.get("gcloud", {})
        conf["gcloud"]["functions"] = conf["gcloud"].get("functions", {})
        conf["gcloud"]["max-instances"] = conf["gcloud"].get("max-instances", click.prompt(
            "Please input the Max Instances your cloud functions should run on"))
        conf["gcloud"]["region"] = conf["gcloud"].get("region", click.prompt(
            "Please enter your default cloudfunction region (europe-west3)"))

        # function layer
        function_name = name if name else click.prompt("Please enter the Name of your cloudfunction")
        function_dict = conf["gcloud"]["functions"].get(function_name, {})

        function_dict["entry-point"] = function_dict.get("entry-point", entrypoint if entrypoint else click.prompt(
            "Please enter your cloudfunction entrypoint (main)"))

        function_dict["env-vars-file"] = function_dict.get("env-vars-file",
                                                           env_vars_file if env_vars_file else click.prompt(
                                                               "Enter the name of your environment variables file"))

        function_dict["memory"] = function_dict.get("memory", memory if memory else click.prompt(
            "Please enter your cloudfunction memory usage (512MB)"))

        function_dict["runtime"] = function_dict.get("runtime", runtime if runtime else click.prompt(
            "Please enter your cloudfunction runtime (python311)"))

        function_dict["trigger"] = function_dict.get("trigger", trigger if trigger else click.prompt(
            "Please enter your cloudfunction trigger type (http)"))
        function_dict["source"] = function_dict.get("source", source if source else click.prompt(
            "Enter the directory of your cloudfuntion"))

        conf["gcloud"]["functions"][function_name] = function_dict

        config[profile] = conf
        config.migrate()
        echo_positive("Your cloudfunction creation was succesfull, if you want to add more flags, "
                      "add them in your project.json under")

