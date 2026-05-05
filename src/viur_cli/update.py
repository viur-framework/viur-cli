import click
import subprocess
import sys
import re
from pathlib import Path
from .conf import config
from .cli import cli
from .utils import echo_error, echo_info, echo_warning


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(["requirements"]))
@click.argument("profile", default='default')
@click.argument("additional_args", nargs=-1)
def update(action, profile, additional_args):
    """
    Update project-specific files and dependencies.

    This command allows you to update project-specific files and dependencies for a specified project configuration.
    Currently, it supports the 'requirements' action, which is used to update the requirements using uv.

    The `update` command performs the specified 'action' to update project-specific files or dependencies.
    It ensures that the specified project configuration exists and uses modern uv tooling.

    Note:
        - Requires uv to be installed: pip install uv
        - Uses pyproject.toml as the source of truth for dependencies
        - Generates requirements.txt with hashes for security
    """
    if action == "requirements":
        create_req(True, profile)


def create_req(yes, profile, confirm_value=True):
    """
    Generate a requirements.txt using uv from pyproject.toml.

    This function generates a requirements.txt file based on the project's pyproject.toml.
    It uses uv for modern, fast dependency resolution with hash generation.

    :param yes: bool
        If True, skip confirmation prompt.
    :param profile: str
        The project profile to use.
    :param confirm_value: bool, default: True
        Default value for confirmation prompt.

    Note:
    - Requires uv to be installed
    - Uses pyproject.toml as dependency source
    - Generates hashes for all dependencies for security
    - Post-processes requirements to handle extras compatibility

    :return: None
    """
    conf = config.get_profile(profile)
    dist_folder = Path(conf["distribution_folder"])
    requirements_file = dist_folder / "requirements.txt"

    # Check for pyproject.toml in current directory or common locations
    possible_pyproject_paths = [
        Path("pyproject.toml"),
        Path("./pyproject.toml"),
        Path("../pyproject.toml"),
    ]

    pyproject_file = None
    for path in possible_pyproject_paths:
        if path.exists():
            pyproject_file = path
            break

    if pyproject_file is None:
        echo_error("pyproject.toml not found!")
        echo_error("Searched in: " + ", ".join(str(p) for p in possible_pyproject_paths))
        echo_error("Please create a pyproject.toml file with your dependencies.")
        echo_info("Example pyproject.toml:")
        echo_info("""
[project]
name = "your-project"
version = "1.0.0"
dependencies = [
    "viur-core>=3.6.0",
]
""")
        sys.exit(1)

    # Ensure distribution folder exists
    dist_folder.mkdir(parents=True, exist_ok=True)

    if not yes and not click.confirm(
        text=f"Would you like to regenerate {requirements_file}?",
        default=confirm_value
    ):
        return

    # Check if uv is installed
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        echo_info(f"Using {result.stdout.strip()}")
    except FileNotFoundError:
        echo_error("uv is not installed!")
        echo_error("Please install it with one of the following methods:")
        echo_info("  - pip install uv")
        echo_info("  - curl -LsSf https://astral.sh/uv/install.sh | sh")
        echo_info("  - Visit: https://github.com/astral-sh/uv")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        echo_error(f"Error checking uv version: {e.stderr}")
        sys.exit(1)

    echo_info(f"Generating {requirements_file} from {pyproject_file.resolve()} using uv...")

    # Generate requirements.txt with uv
    cmd = [
        "uv",
        "pip",
        "compile",
        str(pyproject_file),
        "--generate-hashes",
        "--output-file",
        str(requirements_file)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        if result.stdout:
            echo_info(result.stdout.strip())

        echo_info(f"✓ Successfully generated {requirements_file}")

    except subprocess.CalledProcessError as e:
        echo_error(f"Error running uv compile:")
        if e.stderr:
            echo_error(e.stderr)
        echo_error("Please check your pyproject.toml for syntax errors or dependency conflicts")
        sys.exit(1)

    # Post-process requirements.txt to handle extras
    try:
        generated_requirements = requirements_file.read_text()
        additional_lines = []

        for line in generated_requirements.splitlines():
            if "]==" in line:
                # Add dependency without extras for compatibility
                cleaned_line = re.sub(r"\[.*?\]", "", line)
                additional_lines.append(cleaned_line)

        if additional_lines:
            generated_requirements += "\n# Dependencies without extras for compatibility\n"
            generated_requirements += "\n".join(additional_lines) + "\n"
            requirements_file.write_text(generated_requirements)
            echo_info(f"✓ Post-processed {len(additional_lines)} dependencies with extras")

        echo_info(f"✓ {requirements_file} successfully generated and ready for deployment")

    except Exception as e:
        echo_error(f"Error post-processing requirements.txt: {e}")
        sys.exit(1)

    # Optional: Verify the generated requirements
    verify_requirements(requirements_file)


def verify_requirements(requirements_file: Path):
    """
    Verify the generated requirements.txt file.

    This function performs basic validation on the generated requirements file:
    - Checks if file exists and is not empty
    - Counts number of dependencies
    - Verifies hash presence

    :param requirements_file: Path
        Path to the requirements.txt file to verify
    """
    if not requirements_file.exists():
        echo_error(f"Requirements file not found: {requirements_file}")
        return

    try:
        content = requirements_file.read_text()

        if not content.strip():
            echo_warning("Requirements file is empty!")
            return

        lines = [line.strip() for line in content.splitlines()
                if line.strip() and not line.strip().startswith('#')]

        # Count dependencies (lines with ==)
        dependencies = [line for line in lines if '==' in line]
        hashed_deps = [line for line in lines if '--hash=' in line]

        echo_info(f"✓ Verified {len(dependencies)} dependencies")
        if hashed_deps:
            echo_info(f"✓ {len(hashed_deps)} dependencies have security hashes")
        else:
            echo_warning("No hashes found in requirements! Consider regenerating with --generate-hashes")

    except Exception as e:
        echo_warning(f"Could not verify requirements file: {e}")
