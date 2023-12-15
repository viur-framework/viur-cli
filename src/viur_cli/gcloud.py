import subprocess
import click
from . import cli
from .conf import config


@cli.group()
def gcloud():
    """FUCK FUCK FUUUUCK"""


@gcloud.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["backup"]))
@click.argument("additional_args", nargs=-1)
@click.argument("profile", default="default")
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
