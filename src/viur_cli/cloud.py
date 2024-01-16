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
    """Manage cloud Actions"""

@cloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["backup"]))
def enable(action):
    """
        Enable specific features for the project.
    """
    if action == "backup":
        enable_gcp_backup()

def enable_gcp_backup():
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

@cloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["backup"]))
def disable(action):
    """
        Disable specific features for the project.
    """
    if action == "backup":
        disable_gcp_backup()

def disable_gcp_backup():
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

    print('Success! Gcloud Backups have been disabled')



@cloud.command(context_settings={"ignore_unknown_options": True})#
@click.argument("action", type=click.Choice(["gcsetup"]))
def setup(action):
    if action == "gcsetup":
        gcloud_setup()


def gcloud_setup():
    project = input("Enter PROJECT_ID").strip()

    if not project:
        echo_fatal("Usage: python scrtipt.py PROJECT_ID")
        return

    echo_info("Check if user is authorized with gcloud....")

    try:
        run_command("gcloud auth print-access-token >/dev/null 2>&1")
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
        run_command(f"gcloud app describe --project={project} >/dev/null 2>&1")
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
            print("User aborted.")
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
    run_command("pushd deploy")
    for yaml in ["cron.yaml", "queue.yaml", "index.yaml"]:
        run_command(f"gcloud app deploy -q --project={project} {yaml} >/dev/null 2>&1")

    echo_info("Check if app engine default credentials are set...")
    try:
        run_command("gcloud auth application-default print-access-token >/dev/null 2>&1")

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
        "   viur runv \n"
        "At the first run, it might happen that some functions are\n"
        "causing error 500 because indexes are not immediately\n"
        "served. Therefore, maybe wait a few minutes.\n"
        "Have a nice day.\n")

def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")

@cloud.command()
@click.argument("action", type=click.Choice(['app', 'index', 'cron', 'queue', 'cloudfunction']))
@click.argument("profile", default='develop')
@click.argument("additional_args", nargs=-1)
@click.option("--ext", "-e", default=None)
@click.option("--yes", "-y", is_flag=True, default=False)
@click.option("--name", "-n", default=None)
def deploy(action, profile, name, ext, yes, additional_args):

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
            f'--no-promote {" ".join(additional_args)} {conf["distribution_folder"]} {"-q" if yes else ""}')

    if action == "cloudfunction":
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
    """Builds the deployment command string for the cloud function."""

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

#create cloudfunction entry in project.json
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

    if action == "function":
        conf = config.get_profile(profile)
        ## First layer initialization:
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
