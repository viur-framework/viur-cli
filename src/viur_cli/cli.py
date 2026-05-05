import re
import subprocess
import click
from .conf import *
from .version import __version__
from .version import MINIMAL_UV
import semver
import pprint
import os
from pathlib import Path


@click.group(invoke_without_command=True, no_args_is_help=True,
             context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__)
@click.pass_context
def cli(ctx):
    """Manage and operate ViUR projects from a single command line.

    Reads `project.json` for per-profile settings (deploy targets, build
    pipelines, packaged ViUR frontends). Run `viur project list` to see
    the resolved configuration of a profile.
    """
    uv_version = subprocess.check_output(["uv", "self", "version"]).decode("utf-8")
    match = re.search(r"\b(\d+\.\d+\.\d+)\b", uv_version)
    sys_uv = match.group(1)

    if semver.compare(sys_uv, MINIMAL_UV) < 0:
        echo_warning(
            f"Your uv Version does not match the recommended uv version. \n"
            f"This mismatch may cause Errors, please consider updating your Systems uv version \n"
            f"Your Version: {sys_uv}\n"
            f"Recommended Version: {MINIMAL_UV}"
        )


@cli.command()
@click.argument("action", type=click.Choice(['list']))
@click.argument("profile", default="default")
def project(action, profile):
    """Inspect the resolved project.json configuration for a profile."""
    project_config = config.get_profile(profile)
    if action == "list":
        echo_info(f"These are the Settings for {profile} profile")
        pprint.pprint(project_config)


@cli.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish', 'auto']),
              default='auto', help='Shell type (auto-detect if not specified)')
def setup_autocomplete(shell):
    """Install shell tab-completion for the viur CLI.

    Generates Click's completion script for the chosen shell and writes it
    next to the shell's rc file (sourcing it from `~/.bashrc` / `~/.zshrc`,
    or directly into fish's completions dir).

    Args:
        shell: ``bash``, ``zsh``, ``fish``, or ``auto`` (detect from $SHELL).
    """
    # Auto-detect shell if not specified
    if shell == 'auto':
        shell_env = os.environ.get('SHELL', '')
        if 'bash' in shell_env:
            shell = 'bash'
        elif 'zsh' in shell_env:
            shell = 'zsh'
        elif 'fish' in shell_env:
            shell = 'fish'
        else:
            echo_error("Could not auto-detect shell. Please specify with --shell")
            return

    echo_info(f"Setting up autocompletion for {shell}...")

    home = Path.home()

    if shell == 'bash':
        completion_file = home / '.viur-completion.bash'
        rc_file = home / '.bashrc'

        # Generate completion script
        completion_script = subprocess.run(
            ['viur'],
            env={**os.environ, '_VIUR_COMPLETE': 'bash_source'},
            capture_output=True,
            text=True
        )

        if completion_script.returncode != 0:
            echo_error("Failed to generate bash completion script")
            return

        # Write completion script
        completion_file.write_text(completion_script.stdout)

        # Add to .bashrc if not already present
        source_line = f'source {completion_file}\n'
        if rc_file.exists():
            rc_content = rc_file.read_text()
            if str(completion_file) not in rc_content:
                with rc_file.open('a') as f:
                    f.write(f'\n# viur CLI autocompletion\n')
                    f.write(source_line)
                echo_success(f"Added autocompletion to {rc_file}")
            else:
                echo_info("Autocompletion already configured in .bashrc")
        else:
            echo_warning(".bashrc not found. Please add the following line manually:")
            echo_info(source_line)

    elif shell == 'zsh':
        completion_file = home / '.viur-completion.zsh'
        rc_file = home / '.zshrc'

        # Generate completion script
        completion_script = subprocess.run(
            ['viur'],
            env={**os.environ, '_VIUR_COMPLETE': 'zsh_source'},
            capture_output=True,
            text=True
        )

        if completion_script.returncode != 0:
            echo_error("Failed to generate zsh completion script")
            return

        # Write completion script
        completion_file.write_text(completion_script.stdout)

        # Add to .zshrc if not already present
        source_line = f'source {completion_file}\n'
        if rc_file.exists():
            rc_content = rc_file.read_text()
            if str(completion_file) not in rc_content:
                with rc_file.open('a') as f:
                    f.write(f'\n# viur CLI autocompletion\n')
                    f.write(source_line)
                echo_success(f"Added autocompletion to {rc_file}")
            else:
                echo_info("Autocompletion already configured in .zshrc")
        else:
            echo_warning(".zshrc not found. Please add the following line manually:")
            echo_info(source_line)

    elif shell == 'fish':
        completion_dir = home / '.config' / 'fish' / 'completions'
        completion_file = completion_dir / 'viur.fish'

        # Create directory if it doesn't exist
        completion_dir.mkdir(parents=True, exist_ok=True)

        # Generate completion script
        completion_script = subprocess.run(
            ['viur'],
            env={**os.environ, '_VIUR_COMPLETE': 'fish_source'},
            capture_output=True,
            text=True
        )

        if completion_script.returncode != 0:
            echo_error("Failed to generate fish completion script")
            return

        # Write completion script
        completion_file.write_text(completion_script.stdout)
        echo_success(f"Installed fish completion to {completion_file}")

    echo_info("\nAutocompletion setup complete!")
    echo_info("Please restart your shell or run:")
    if shell in ['bash', 'zsh']:
        echo_info(f"  source {completion_file}")


@cli.command()
def uninstall_autocomplete():
    """Remove shell autocompletion for the viur CLI."""
    home = Path.home()
    removed = False

    # Remove completion files
    completion_files = [
        home / '.viur-completion.bash',
        home / '.viur-completion.zsh',
        home / '.config' / 'fish' / 'completions' / 'viur.fish'
    ]

    for file in completion_files:
        if file.exists():
            file.unlink()
            echo_info(f"Removed {file}")
            removed = True

    # Clean up shell rc files
    rc_files = [
        (home / '.bashrc', '.viur-completion.bash'),
        (home / '.zshrc', '.viur-completion.zsh')
    ]

    for rc_file, completion_name in rc_files:
        if rc_file.exists():
            content = rc_file.read_text()
            if completion_name in content:
                # Remove the source line and the comment before it
                lines = content.splitlines()
                new_lines = []
                skip_next = False

                for i, line in enumerate(lines):
                    if '# viur CLI autocompletion' in line:
                        skip_next = True
                        continue
                    if skip_next and completion_name in line:
                        skip_next = False
                        continue
                    new_lines.append(line)

                rc_file.write_text('\n'.join(new_lines))
                echo_info(f"Cleaned up {rc_file}")
                removed = True

    if removed:
        echo_success("Autocompletion uninstalled successfully")
    else:
        echo_info("No autocompletion files found")


@cli.command()
def autocomplete_info():
    """Show autocompletion status and instructions."""
    echo_info("viur CLI Autocompletion Information")
    echo_info("=" * 40)

    shell = os.environ.get('SHELL', 'unknown')
    echo_info(f"Current shell: {shell}")

    home = Path.home()
    completion_files = {
        'bash': home / '.viur-completion.bash',
        'zsh': home / '.viur-completion.zsh',
        'fish': home / '.config' / 'fish' / 'completions' / 'viur.fish'
    }

    installed = []
    for shell_type, file_path in completion_files.items():
        if file_path.exists():
            installed.append(shell_type)

    if installed:
        echo_success(f"Autocompletion installed for: {', '.join(installed)}")
    else:
        echo_warning("No autocompletion installed")
        echo_info("\nTo install, run:")
        echo_info("  viur setup-autocomplete")


def main() -> None:
    """Entry point used by the ``viur`` console script.

    Imports each command module explicitly so its ``@cli.command`` /
    ``@cli.group`` decorators bind to the root ``cli`` group above. This
    replaces the v2 pattern that relied on star-imports in
    ``__init__.py`` to trigger the same decorator side-effects.
    """
    # Side-effect imports — decorators run on module load.
    from viur_cli import build  # noqa: F401
    from viur_cli import cloud  # noqa: F401
    from viur_cli import local  # noqa: F401
    from viur_cli import package  # noqa: F401
    from viur_cli import setup  # noqa: F401
    from viur_cli import update  # noqa: F401
    from viur_cli import deprecated  # noqa: F401
    from viur_cli.scriptor import script  # noqa: F401

    cli()
