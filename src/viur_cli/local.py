import json

import click
import requests
import shutil
import subprocess

from .conf import config
from .cli import cli
from . import utils
from .utils import echo_warning, echo_error, echo_fatal


def get_user_info():
    """Fetch the gcloud-authenticated user's profile via Google's userinfo endpoint."""
    gcloud_auth_process = subprocess.run(
        ["gcloud", "auth", "application-default", "print-access-token"],
        capture_output=True,
        text=True,
        check=True,
    )
    auth_token = gcloud_auth_process.stdout.strip()

    response = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        params={"alt": "json"},
        headers={"Authorization": f"Bearer {auth_token}"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("profile", default="default")
@click.argument("additional_args", nargs=-1)
def run(profile, additional_args):
    """
    Start your application locally.
    The 'run' command launches your ViUR application locally specified configuration and optional arguments.
    This Enforces the Usage of gcloud tool
    """
    try:
        echo_warning(
            f"You are using the development Server with your default account: {get_user_info()['email']}"
        )
    except:
        echo_fatal(
            f"It seems you are not Using an appropriate account. "
            f"Please install the 'gcloud' tool or Log in with an appropriate account."
        )

    conf = config.get_profile(profile)
    additional_args = list(additional_args)

    if appyaml := conf.get("appyaml"):
        additional_args.append(f"--appyaml={appyaml}")
    if conf.get("port"):
        additional_args.append(f"--port={conf['port']}")
    if conf.get("gunicorn_port"):
        additional_args.append(f"--gunicorn_port={conf['gunicorn_port']}")

    utils.system(
        f"app_server -A={conf['application_name']} {conf['distribution_folder']} {' '.join(additional_args)}"
    )


@cli.command()
@click.argument("profile", default="default")
def env(profile):
    """
    Check the local environment for ViUR development.

    The 'env' command provides information about the versions tools and dependencies, such as ViUR-CLI, app_server,
    git, Python, npm, node, and more. It checks the availability of these tools and reports their versions.

    """

    valid_icon = "\U00002714"
    failed_icon = "\U0000274c"

    conf = config.get_profile(profile)
    click.echo(f"Project Info:\n--------------------------------")
    try:
        click.echo(f"format: {config['format']}")
        for entry in conf["builds"]:
            if entry in conf["builds"]:
                click.echo(f"\n {entry}: {conf['builds'][entry]['version'] } ")

    except Exception as e:
        echo_error("Error while collecting viur info")

        echo_error(str(e))
    click.echo(f"\nCurrent Environment:\n--------------------------------")

    # viur-cli
    if shutil.which("viur"):
        app_server_version = subprocess.check_output(["viur", "--version"]).decode(
            "utf-8"
        )
        click.echo(f"{valid_icon} {app_server_version}")
    else:
        click.echo(f"{failed_icon} ViUR-CLI")

    # app_server
    if shutil.which("app_server"):
        app_server_version = subprocess.check_output(["app_server", "-V"]).decode(
            "utf-8"
        )
        click.echo(f"{valid_icon} {app_server_version}")
    else:
        click.echo(f"{failed_icon} app_server")

    # git
    if shutil.which("git"):
        git_version = subprocess.check_output(["git", "--version"]).decode("utf-8")
        click.echo(f"{valid_icon} {git_version}")
    else:
        click.echo(f"{failed_icon}")

    # python3
    if shutil.which("python3"):
        npm_version = subprocess.check_output(["python3", "-V"]).decode("utf-8")
        click.echo(f"{valid_icon} python3 > {npm_version}")
    else:
        click.echo(f"{failed_icon}")

    # python
    if shutil.which("python"):
        npm_version = subprocess.check_output(["python", "-V"]).decode("utf-8")
        click.echo(f"{valid_icon} python > {npm_version}")
    else:
        click.echo(f"{failed_icon}")

    # python3
    if shutil.which("pyenv"):
        pyenv_version = subprocess.check_output(["pyenv", "--version"]).decode("utf-8")
        click.echo(f"{valid_icon} {pyenv_version}")
    else:
        click.echo(f"{failed_icon}")

    # npm
    if shutil.which("npm"):
        npm_version = subprocess.check_output(["npm", "-v"]).decode("utf-8")
        click.echo(f"{valid_icon} npm {npm_version}")
    else:
        click.echo(f"{failed_icon} npm")

    # node
    if shutil.which("node"):
        npm_version = subprocess.check_output(["node", "-v"]).decode("utf-8")
        click.echo(f"{valid_icon} node {npm_version}")
    else:
        click.echo(f"{failed_icon} node")

    # pnpm
    if shutil.which("pnpm"):
        npm_version = subprocess.check_output(["pnpm", "-v"]).decode("utf-8")
        click.echo(f"{valid_icon} pnpm {npm_version}")
    else:
        click.echo(f"{failed_icon} pnpm (optional)")

    # gcloud
    if shutil.which("gcloud"):
        gcloud_version = (
            subprocess.check_output(["gcloud", "-v"]).decode("utf-8").split("\n\n")[0]
        )
        versionList = []
        for line in gcloud_version.split("\n"):
            if not line:
                continue
            if not line.startswith("Google Cloud SDK"):
                line = " - " + line
            versionList.append(line)
        versionString = "\n".join(versionList)
        click.echo(f"{valid_icon} {versionString}")
    else:
        click.echo(f"{failed_icon} gcloud")

    click.echo(f"\nYour default gcloud user Info:\n--------------------------------")
    for k, v in get_user_info().items():
        click.echo(f"{k}: {v}")


@cli.command()
@click.option("--dev", "-d", is_flag=True, default=False)
def check(dev):
    """
    Perform security checks for vulnerabilities.
    The 'check' command helps you identify and address security vulnerabilities in your project's dependencies.
    """

    if do_checks(dev):
        utils.echo_info("\U00002714 No vulnerabilities found.")


def do_checks(dev=True):
    """Run security checks for Python and npm dependencies.

    Returns True if no vulnerabilities found, False otherwise.
    """
    has_vulnerabilities = False

    # --- Python vulnerability check via pip-audit (PyPA tool, OSV data) ---
    try:
        result = subprocess.run(
            ["uvx", "pip-audit", "--format", "json", "--vulnerability-service", "osv"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        echo_warning("uvx not found; skipping Python vulnerability check.")
    else:
        # pip-audit returncode: 0 = no vulns, 1 = vulns found, anything else = real error.
        if result.returncode not in (0, 1):
            echo_error(
                f"pip-audit failed (exit {result.returncode}): "
                f"{(result.stderr or result.stdout)[:500]}"
            )
        else:
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                echo_error(f"Failed to parse pip-audit output: {e}")
                echo_error(f"Raw output (truncated): {result.stdout[:500]}")
            else:
                deps = data.get("dependencies", [])
                vuln_deps = [d for d in deps if d.get("vulns")]
                total_vulns = sum(len(d["vulns"]) for d in vuln_deps)

                click.echo("\n" + "=" * 60)
                click.echo("Python Security Scan Results (pip-audit, OSV)")
                click.echo("=" * 60)
                click.echo(f"Total Packages:         {len(deps)}")
                click.echo(f"Vulnerable Packages:    {len(vuln_deps)}")
                click.echo(f"Total Vulnerabilities:  {total_vulns}")
                click.echo("=" * 60)

                if vuln_deps:
                    has_vulnerabilities = True
                    click.echo("Run `uvx pip-audit --vulnerability-service osv` for per-package detail.")

    # --- npm vulnerability check ---
    if shutil.which("npm"):
        conf = config.get_profile("default")
        builds = conf.get("builds", {})
        sources_folder = conf.get("sources_folder", "./sources")

        # Collect all npm builds. Empty `source` is valid and means
        # "audit at the sources_folder root" (npm workspace root).
        npm_builds = []
        for build_name, build_config in builds.items():
            if build_config.get("kind") != "npm":
                continue
            source_path = build_config.get("source") or ""
            audit_path = f"{sources_folder}/{source_path}".rstrip("/") if source_path else sources_folder
            npm_builds.append({"name": build_name, "path": audit_path})

        if not npm_builds:
            click.echo("\n" + "=" * 60)
            click.echo("No npm builds found in config - skipping npm audit")
            click.echo("=" * 60)
        else:
            # Run audit for each npm build
            for build in npm_builds:
                try:
                    npm_audit_dir = build["path"]

                    npm_result = subprocess.run(
                        ["npm", "audit", "--json"],
                        capture_output=True,
                        text=True,
                        cwd=npm_audit_dir,
                    )

                    npm_data = json.loads(npm_result.stdout, strict=False)

                    metadata = npm_data.get("metadata", {})
                    npm_vulnerabilities = npm_data.get("vulnerabilities", {})

                    vuln_counts = metadata.get("vulnerabilities", {})
                    dependencies = metadata.get("dependencies", {})

                    total_npm_vulns = vuln_counts.get("total", 0)

                    if total_npm_vulns > 0:
                        has_vulnerabilities = True

                    # Display npm scan summary
                    click.echo("\n" + "=" * 60)
                    click.echo(f"npm Security Scan Results - {build['name']}")
                    click.echo("=" * 60)
                    click.echo(f"Build Path:             {npm_audit_dir}")
                    click.echo(
                        f"Total Dependencies:     {dependencies.get('total', 0)}"
                    )
                    click.echo(f"Total Vulnerabilities:  {total_npm_vulns}")
                    click.echo(
                        f"  Critical:             {vuln_counts.get('critical', 0)}"
                    )
                    click.echo(f"  High:                 {vuln_counts.get('high', 0)}")
                    click.echo(
                        f"  Moderate:             {vuln_counts.get('moderate', 0)}"
                    )
                    click.echo(f"  Low:                  {vuln_counts.get('low', 0)}")
                    click.echo(f"  Info:                 {vuln_counts.get('info', 0)}")
                    click.echo("=" * 60)

                    if total_npm_vulns > 0:
                        click.echo(f"Run `npm audit` in {build['path']} for per-package detail.")

                except FileNotFoundError:
                    echo_warning(f"npm audit directory not found: {build['path']}")
                except json.JSONDecodeError as e:
                    echo_error(
                        f"Error parsing npm audit output for {build['name']}: {e}"
                    )
                except Exception as e:
                    echo_error(
                        f"Unexpected error during npm security check for {build['name']}: {e}"
                    )
    else:
        click.echo("\n" + "=" * 60)
        click.echo("npm not found - skipping npm audit")
        click.echo("=" * 60)

    return not has_vulnerabilities
