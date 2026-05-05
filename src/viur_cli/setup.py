import os
import subprocess
import click
from .cli import cli
from .utils import *


def clean_base(app_id, author=None):
    """Stamp a freshly cloned `viur-base` checkout with the new project's identity.

    Walks the project tree and substitutes ``{{app_id}}`` / ``{{whoami}}``
    / ``{{timestamp}}`` placeholders inside ``.py`` / ``.yaml`` /
    ``.html`` / ``.md`` / ``.sh`` / ``.json`` / ``.js`` / ``.less``
    files, then resets git history to a single ``main`` commit.

    Args:
        app_id: New application-id; also doubles as the working
            directory the function ``chdir``'s into.
        author: Author name. Defaults to the current OS user (or
            ``"viur"`` if that lookup fails).

    Side effects:
        * Modifies files in place under ``<cwd>/<app_id>``.
        * Resets git history to a single ``main`` branch.
        * Removes the original ``README.md`` and renames
          ``viur-project.md`` over it.
        * Deletes ``sys.argv[0]`` (the script that triggered cleanup).
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
        subprocess.check_output(["git", "checkout", "--orphan", "main_tmp"])
        echo_info(subprocess.check_output(["git", "branch", "-D", "main"]).decode().rstrip("\n"))

        subprocess.check_output(["git", "branch", "-m", "main"])
        branch_current = subprocess.check_output(["git", "branch", "--show-current"]).decode().rstrip("\n")
        echo_info(f"Current branch is: {branch_current}")
        echo_info("---")

    echo_info("Generating project documentation...")
    sys.stdout.flush()

    os.remove("README.md")  # Remove README.md if it exists
    os.rename("viur-project.md", "README.md")
    os.remove(sys.argv[0])  # Remove the script itself

    echo_success("Project repository has been set-up now.")


@cli.command()
@click.argument("name")
@click.pass_context
def create(ctx, name):
    """Clone viur-base into ./NAME and run its clean-base.py setup wizard.

    Optionally chains into ``./viur-gcloud-setup.sh NAME`` if confirmed,
    so the project is wired to a fresh GCP project in one shot.
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
