import os
import subprocess
import click
from .cli import cli
from .utils import *


def clean_base(app_id, author=None):
    """
    Sets up a clean ViUR project base.

    Args:
        clean_history (bool, optional): Whether to clean the git history. Defaults to True.
        app_id (str, optional): The application-id to use. If not provided, prompts the user.
        author (str, optional): The author's name to use. If not provided, defaults to the current user.
    """

    try:
        whoami = getpass.getuser()
    except Exception:
        whoami = "viur"

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.chdir(app_id)

    file_list = ["viur-project.md"]
    replacements = {"{{app_id}}": app_id, "{{whoami}}": whoami, "{{timestamp}}": timestamp}

    for subdir, dirs, files in os.walk("."):
        for file in files:
            filepath = subdir + os.sep + file

            if any([filepath.endswith(ext) for ext in
                    [".py", ".yaml", ".html", ".md", ".sh", ".json", ".js", ".less"]]):
                file_list.append(filepath)

    for file_obj in file_list:
        lines = []
        with open(file_obj, "r") as infile:
            for line in infile:
                for src, target in replacements.items():
                    line = line.replace(src, target)
                lines.append(line)
        with open(file_obj, "w") as outfile:
            for line in lines:
                outfile.write(line)

    if os.path.exists(".git"):
        echo_info("Cleaning git history")
        subprocess.check_output("git checkout --orphan main_tmp", shell=True)
        echo_info(subprocess.check_output("git branch -D main", shell=True).decode().rstrip("\n"))

        subprocess.check_output("git branch -m main", shell=True)
        echo_info(f"Current branch is: "
                  f"{subprocess.check_output('git branch --show-current', shell=True).decode().rstrip('\n')}")
        echo_info("---")

    echo_info("Generating project documentation...")
    sys.stdout.flush()

    os.remove("README.md")  # Remove README.md if it exists
    os.rename("viur-project.md", "README.md")
    os.remove(sys.argv[0])  # Remove the script itself

    echo_positive("Project repository has been set-up now.")


@cli.command()
@click.argument("name")
@click.pass_context
def create(ctx, name):
    """
    Create a new ViUR project.

    The 'create' command allows you to create a new ViUR project by cloning the ViUR base project and configuring it.
    You can specify the name of the new project as the 'name' argument.

    The 'create' command performs the following steps:

        1. Clones the ViUR base project from the official GitHub repository.

        2. Configures the new project by running 'clean-base.py'.

        3. Optionally configures the project as a new gcloud project (if confirmed).

    Note:

        - This command initializes the new ViUR project based on the ViUR base project.

        - Make sure to provide a unique project name to avoid conflicts with existing folders.

    """
    if os.path.exists(f'./{name}'):
        echo_error(f'"{name}" Folder already exists. Please use a different name or remove this folder ./{name}')
        return

    # fetch base project
    git_clonne_cmd = ['git', 'clone', f'https://github.com/viur-framework/viur-base.git', name]
    subprocess.run(git_clonne_cmd, check=True)

    wdir = f"{os.getcwd()}/{name}"

    # Run clean-base.py
    clean_base_cmd = ['python3', 'clean-base.py', '-A', f'{name}']
    subprocess.run(clean_base_cmd, check=True, cwd=wdir)

    # Run gcloud config (if confirmed)
    if click.confirm(f'Do you want to configure "{name}" as a new gcloud project?'):
        gcloud_setup_cmd = ['./viur-gcloud-setup.sh', name]
        subprocess.run(gcloud_setup_cmd, check=True, cwd=wdir)
