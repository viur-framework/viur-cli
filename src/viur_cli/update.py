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
    """Regenerate project-managed deploy files (currently `deploy/requirements.txt`).

    \b
    Examples:
      viur update requirements
      viur update requirements live
    """
    if action == "requirements":
        create_req(True, profile)


def create_req(yes, profile, confirm_value=True):
    """Compile pyproject.toml into deploy/requirements.txt with hashes via `uv pip compile`.

    Args:
        yes: Skip the confirmation prompt before regeneration.
        profile: Profile name from ``project.json``; used to resolve
            ``distribution_folder`` (where ``requirements.txt`` lands).
        confirm_value: Default for the confirmation prompt when ``yes``
            is False.

    Side effects:
        * Calls ``uv pip compile pyproject.toml --generate-hashes -o
          deploy/requirements.txt``.
        * Post-processes the result: for any ``foo[extra]==X.Y`` line,
          appends a stripped ``foo==X.Y`` line for callers that don't
          understand extras syntax.
        * Aborts the process via ``sys.exit(1)`` if uv is missing or the
          compile step fails.
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
    """Sanity-check a generated requirements.txt — non-empty, hashes present."""
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
