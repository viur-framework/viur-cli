import json
from pathlib import Path
import subprocess
import os
import string
import time
import click
import yaml
from .conf import config
from .cli import cli
from .utils import echo_success, echo_warning, echo_fatal, echo_error, echo_info, replace_vars
from .update import create_req


@cli.group()
def cloud():
    """Manage Google Cloud resources for a ViUR project (deploy, IAM, backup, datastore)."""


@cloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["bucket2bucket", "bucket2local", "local2bucket"]))
@click.argument("profile", default="default")
def copy(action, profile):
    """Copy data between Cloud Storage buckets or between bucket and Datastore."""
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
    """Prompt the user to confirm they are signed in to gcloud as an admin."""
    return click.confirm("Are you logged in with your gcloud admin account?", default=False, show_default=True)


def storage_copy():
    """Interactively copy a Cloud Storage bucket to another bucket via `gsutil cp -r`."""
    # https://console.cloud.google.com/transfer/jobs
    source = click.prompt('Source bucketname')
    target = click.prompt('Target bucketname')
    if not click.confirm(text=f"Copy from {source} to {target}", default=True):
        print("Abort ...")
        return 0
    print(f"gsutil -m cp -r gs://{source}/ gs://{target}/")
    subprocess.run(
        ["gsutil", "-m", "cp", "-r", f"gs://{source}", f"gs://{target}"],
        check=False,
    )


def datastore_import(profile):
    """Import a Datastore export (referenced by `overall_export_metadata`) into the profile's project."""
    conf = config.get_profile(profile)
    target = click.prompt('path to overall_export_metadata')
    subprocess.run(
        ["gcloud", "datastore", "import", f"gs://{target}", f"--project={conf['application_name']}"],
        check=False,
    )


def datastore_export(profile):
    """Export the profile's Datastore to a bucket, suffixed with a manual timestamp."""
    conf = config.get_profile(profile)
    target = click.prompt('bucketname')
    timestamp = f'{datetime.now().strftime("%Y%m%d-%H%M%S")}-manual'
    format = "default"
    subprocess.run(
        ["gcloud", "datastore", "export", f"gs://{target}/{timestamp}-{format}",
         f"--format={format}", f"--project={conf['application_name']}"],
        check=False,
    )


@cloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["backup"]))
def enable(action):
    """Enable an optional cloud feature on the active project (currently only `backup`)."""
    if action == "backup":
        enable_gcp_backup()


def enable_gcp_backup():
    """Provision the backup bucket and grant the App Engine service account the required IAM roles.

    Side effects:
        * Creates `gs://backup-dot-<application_name>` in `EUROPE-WEST3`
          via `gsutil mb`.
        * Adds the policy bindings ``roles/storage.admin`` and
          ``roles/datastore.importExportAdmin`` to
          ``<application_name>@appspot.gserviceaccount.com``.

    Reads the ``application_name`` field from the ``default`` profile.
    Errors during bucket creation or role binding are printed but do not
    raise — the caller continues so partial setups can be inspected
    manually.
    """
    # Load the project Config
    conf = config.get_profile("default")

    # Create helper Variables
    project_id = conf["application_name"]
    bucket_name = f'backup-dot-{project_id}'

    # Create the Backup Bucket
    try:
        result = subprocess.run(
            ["gsutil", "mb", "-l", "EUROPE-WEST3", "-p", project_id, f"gs://{bucket_name}"],
            capture_output=True,
        )
        if result.returncode != 0:
            echo_error('Error creating bucket.')

    except Exception as e:
        print(f'An Error Occured:\n {e} Please make sure you have the correct Google Cloud Access rights')

    # Helper Variables for IAM
    iam_roles = ["roles/storage.admin", "roles/datastore.importExportAdmin"]
    service_worker_mail = f'{project_id}@appspot.gserviceaccount.com'

    for r in iam_roles:
        try:
            subprocess.run(
                ["gcloud", "projects", "add-iam-policy-binding", project_id,
                 "--member", f"serviceAccount:{service_worker_mail}", "--role", r],
                capture_output=True,
            )

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
    """Bootstrap a fresh project on GCP by deploying its cron and queue configs."""
    deployments = ["cron", "queue", "cron"]
    if service == "gcloud":
        for element in deployments:
            subprocess.run(["viur", "cloud", "deploy", element, profile, "-y"], check=False)


@cloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("service", type=click.Choice(["gcloud"]), default="gcloud")
@click.argument("option", type=click.Choice(["datastore"]), default="datastore")
@click.argument("profile", default="default")
def cleanup(service, option, profile):
    """Run `gcloud datastore indexes cleanup` against `deploy/index.yaml`."""
    conf = config.get_profile(profile)

    if service == "gcloud" and option == "datastore":
        run_command([
            "gcloud", "datastore", "indexes", "cleanup", "deploy/index.yaml",
            f"--project={conf['application_name']}",
        ])


@cloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["backup"]))
def disable(action):
    """Disable an optional cloud feature on the active project (currently only `backup`)."""
    if action == "backup":
        disable_gcp_backup()


def disable_gcp_backup():
    """Tear down the backup bucket and revoke the App Engine service account's role bindings.

    Inverse of :func:`enable_gcp_backup`. Removes ``gs://backup-dot-<application_name>``
    and the ``roles/storage.admin`` / ``roles/datastore.importExportAdmin``
    bindings for ``<application_name>@appspot.gserviceaccount.com``.

    Errors are printed but not raised.
    """

    # Load the project Config
    conf = config.get_profile("default")

    # Create helper Variables
    project_id = conf["application_name"]
    bucket_name = f'backup-dot-{project_id}'

    # Remove the Backup Bucket
    try:
        result = subprocess.run(
            ["gsutil", "rm", "-r", f"gs://{bucket_name}"],
            capture_output=True,
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
        try:
            subprocess.run(
                ["gcloud", "projects", "remove-iam-policy-binding", project_id,
                 "--member", f"serviceAccount:{service_worker_mail}", "--role", r],
                capture_output=True,
            )

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
    """Apply IAM-role bindings from `<profile>_roles.json` back to the project."""
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
    """Read information from the active cloud project (currently: IAM roles)."""

    if action == "gcroles":
        gcloud_get_roles(profile)


def gcloud_get_roles(profile):
    """Dump the project's IAM policy as a member-keyed JSON file.

    Calls ``gcloud projects get-iam-policy``, transforms the result from
    role-keyed (``[{role, members}]``) to member-keyed
    (``[{members, role}]``), and writes it to ``./<profile>_roles.json``
    in the current working directory.

    Edit the JSON, then push the result back via
    ``viur cloud setup gcroles <profile>``.

    Args:
        profile: Profile name from ``project.json`` to determine the
            target ``application_name``.
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

                echo_success(f"You can now watch your gcloud Roles Setup in your '{json_file_path}' file ")

        except yaml.YAMLError as e:
            echo_error(f"An error occurred during YAML to Dictionary transformation: {e}")

        finally:
            # Delete the temporary YAML file
            if os.path.exists(yaml_file_path):
                os.remove(yaml_file_path)

    except subprocess.CalledProcessError:
        echo_error("An error occurred while fetching Role data")


def gcloud_setup_roles(profile):
    """Push IAM roles from `<profile>_roles.json` back to the project.

    Reads the member-keyed JSON written by :func:`gcloud_get_roles`,
    converts it into the role-keyed YAML format expected by ``gcloud
    projects set-iam-policy``, and applies it to the profile's project.

    Args:
        profile: Profile name from ``project.json``.

    Raises:
        json.JSONDecodeError: If ``<profile>_roles.json`` is invalid.
        yaml.YAMLError: If the temporary YAML output can't be written.
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
    """Reshape `bindings: [{role, members}]` into member-keyed form for editing."""
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
    """Inverse of :func:`transform_yaml_to_dict` — reshape member-keyed back to role-keyed."""
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


def run_command(command):
    """Run a command and return its captured stdout.

    Args:
        command: Argv list passed to ``subprocess.check_output`` (no shell
            interpretation, no string-form support).

    Returns:
        The raw stdout bytes on success, or ``None`` if the command exits
        non-zero (the error is printed to stdout).
    """
    try:
        return subprocess.check_output(command)
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
    """Deploy app, index, cron, queue, or a cloudfunction to Google Cloud.

    \b
    Examples:
      viur cloud deploy app dev
      viur cloud deploy index live --yes
      viur cloud deploy cloudfunction dev --name=billing
      viur cloud deploy app dev --skip_checks --ext=hotfix-2026-05-05

    Action-specific behaviour:

    * ``app`` runs `viur check` first (unless ``--skip_checks``) and then
      ``gcloud app deploy`` against ``conf['distribution_folder']``. The
      version label resolves ``$(...)`` variables in
      ``project.json``'s ``version`` field. ``--ext`` appends a suffix.
    * ``index`` reads ``deploy/index.yaml`` and sorts/dedupes index
      definitions by kind before deploy.
    * ``cron`` / ``queue`` deploy the matching ``deploy/<action>.yaml``.
    * ``cloudfunction`` requires ``--name`` to point at a function entry
      defined in ``project.json`` under ``gcloud.functions``.
    """
    conf = config.get_profile(profile)

    if action == "app":
        if not skip_checks:
            from .local import do_checks
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
            deploy_argv = [
                "gcloud", "app", "deploy",
                f"--project={conf['application_name']}",
                f"--version={version}",
                "--no-promote",
                *additional_args,
                conf["distribution_folder"],
            ]
            if yes:
                deploy_argv.append("-q")
            subprocess.run(deploy_argv, check=False)
        finally:
            if app_yaml_tmp is not None:
                app_yaml_tmp.unlink()
            if app_yaml_hidden is not None:
                app_yaml_hidden.rename(app_yaml)

    elif action == "cloudfunction":
        subprocess.run(build_deploy_command(name, conf["gcloud"]), check=False)

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

        deploy_argv = [
            "gcloud", "app", "deploy",
            f"--project={conf['application_name']}",
            *additional_args,
            yaml_file,
        ]
        if yes:
            deploy_argv.append("-q")
        subprocess.run(deploy_argv, check=False)


def build_deploy_command(name, conf):
    """Build the `gcloud run deploy` argv list for a cloudfunction entry.

    Args:
        name: Function name. If empty, the user is prompted interactively.
            Must be a key in ``conf['functions']``.
        conf: The ``gcloud`` block from a profile, expected to contain
            ``region``, ``max-instances``, and ``functions[<name>]`` with
            arbitrary additional flag/value pairs.

    Returns:
        Argv list ready to pass to ``subprocess.run``. Per-flag rules:

        * ``gen``: emitted as ``--gen<value>`` (e.g. ``--gen2``)
        * ``trigger`` / ``update`` / ``set`` / ``remove``: emitted as
          ``--<key>-<value>`` (e.g. ``--trigger-http``)
        * any other key: emitted as ``--<key>=<value>``
    """

    if not name:
        name = click.prompt("Please enter the name of the cloudfunction you want to deploy")

    if name not in conf["functions"]:
        echo_fatal(f"The cloudfunction {name} was not found your project.json\n "
                   f"You can create a cloudfunction entry by calling 'viur cloud create function'")

    command = [
        "gcloud", "run", "deploy", name,
        f"--region={conf['region']}",
        f"--max-instances={conf['max-instances']}",
    ]

    for k, v in conf["functions"][name].items():
        if k == "gen":
            # historic single-arg form: e.g. `--gen2`
            command.append(f"--{k}{v}")
        elif k in ["trigger", "update", "set", "remove"]:
            # historic compound form: e.g. `--trigger-http`
            command.append(f"--{k}-{v}")
        else:
            command.append(f"--{k}={v}")

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
    """Add a cloudfunction entry to project.json (interactive prompts for missing fields).

    Each unset CLI option falls back to a `click.prompt`. The result is
    persisted under ``gcloud.functions.<name>`` in the active profile.
    """
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
        echo_success("Your cloud function creation was successful, if you want to add more flags, "
                      "add them in your project.json")
