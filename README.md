<div align="center">
    <img src="https://github.com/viur-framework/viur-artwork/raw/main/icons/icon-cli.svg" height="196" alt="A hexagonal logo of the viur-cli" title="viur-cli">
    <h1>viur-cli</h1>
    <a href="https://pypi.org/project/viur-cli/">
        <img alt="Badge showing current PyPI version" title="PyPI" src="https://img.shields.io/pypi/v/viur-cli">
    </a>
    <a href="LICENSE">
        <img src="https://img.shields.io/github/license/viur-framework/viur-cli" alt="Badge displaying the license" title="License badge">
    </a>
    <br>
    Command-line interface for <a href="https://www.viur.dev">ViUR framework</a> project maintenance.
</div>

## What it is

A ViUR project has a handful of recurring chores: start it locally, build its
frontends, install the admin bundle, regenerate the requirements for App Engine,
deploy to Google Cloud, audit the dependencies. Each of them is a different tool
with its own arguments, and each needs the same three facts about the project:
which App Engine project it belongs to, where the deploy folder is, what the
version string is.

`viur-cli` puts these facts into one file, `project.json`, and puts the chores
behind one command, `viur`. The file holds a `default` profile and any number of
named profiles on top of it, so `viur cloud deploy app live` and
`viur cloud deploy app develop` differ in one argument and not in a checklist.

What comes with it:

- **Profiles.** Every profile inherits `default` and overrides what differs,
  typically `application_name` and `version`.
- **Builds in declaration order.** The `builds` section lists npm bundles and
  shell steps; `viur build release` runs them top to bottom.
- **Frontend bundles as packages.** `viur admin install`, `viur vi install` and
  `viur scriptor install` fetch a released bundle from GitHub and unpack it into
  the deploy folder, pinned to the version recorded in `project.json`.
- **Version strings with placeholders.** `live-$(year)-$(month)-$(day)` or
  `dev-$(user)-$(ref)` are resolved at deploy time.
- **A security gate.** `viur check` runs `pip-audit` over the Python
  environment and `npm audit` over every npm build; `viur cloud deploy app`
  runs it first, then regenerates `deploy/requirements.txt`, then uploads.

## Requirements

| What | What for |
|---|---|
| Python 3.11 or newer | the CLI itself |
| [`uv`](https://docs.astral.sh/uv/) 0.9.15 or newer | installs the CLI and regenerates `deploy/requirements.txt` |
| [`gcloud`](https://cloud.google.com/sdk) | `viur run` (login check) and everything under `viur cloud` |
| `git` | `viur create` and the `$(ref)` placeholder |
| `npm` | builds of `kind: npm` and their audit in `viur check` |
| [`app_server`](https://github.com/viur-framework/viur-app_server) | the local development server behind `viur run`; installed as a dependency of `viur-cli` |

macOS and Linux. The CLI warns at start when `uv` is older than the version it
was tested with.

## Installation

Inside a ViUR project, as a development dependency:

```
uv add --dev viur-cli
uv run viur --version
```

Or once for the user, independent of any project:

```
uv tool install viur-cli
```

Updating is `uv lock --upgrade-package viur-cli` in the project, or
`uv tool upgrade viur-cli` for the global install.

Coming from v2: the `project.json` format is unchanged, but v3 is `uv` only and
a project still on `Pipfile` has to migrate first. The steps and the renamed
commands are in the [migration guide](https://viur-framework.github.io/viur-cli/migration/v2-to-v3/).

## Getting started

```
viur create my-project        clone viur-base and run its setup wizard
cd my-project
viur admin install            fetch the admin frontend into deploy/admin
viur run                      start the app locally via app_server
viur build release            run the build steps of project.json
viur cloud deploy app         audit and deploy the default profile
```

`viur-base` brings the `project.json` along and the wizard fills in the
project name. From then on every `viur` command finds the file by walking up
from the current directory, so the commands work from any subfolder of the
project.

`viur run` needs an active `gcloud auth login`, because the local app_server
talks to Google Cloud with that account. It tells you which account it found.

## Commands

The reference is generated from the code and lives at
<https://viur-framework.github.io/viur-cli/commands/>. `viur -h` and
`viur <command> -h` show the same texts. In short:

| Command | Effect |
|---|---|
| `viur create <name>` | clone `viur-base` into `./<name>` and run its setup wizard |
| `viur run [profile]` | start the app locally via `app_server` |
| `viur check [--dev]` | audit Python and npm dependencies for known vulnerabilities |
| `viur build release [profile]` | run every entry of the profile's `builds` section in declaration order |
| `viur build app <name>` | run a single build entry |
| `viur build clean [name]` | drop build artifacts of one or all entries |
| `viur admin`, `viur vi`, `viur scriptor` | `install [version]` or `update` the respective frontend bundle |
| `viur cloud deploy <app\|index\|cron\|queue\|cloudfunction>` | deploy to Google Cloud; `--ext` appends to the version, `--yes` skips prompts, `--skip_checks` skips the audit |
| `viur cloud init` | bootstrap a fresh App Engine project by deploying its cron and queue configs |
| `viur cloud create function` | add a cloud function entry to `project.json` |
| `viur cloud enable\|disable backup` | manage the backup buckets of the active project |
| `viur cloud get\|setup gcroles` | export IAM role bindings to `<profile>_roles.json`, or apply them back |
| `viur cloud copy <bucket2bucket\|bucket2local\|local2bucket>` | copy data between buckets, or between a bucket and the Datastore |
| `viur cloud cleanup` | run `gcloud datastore indexes cleanup` against `deploy/index.yaml` |
| `viur update requirements [profile]` | compile `pyproject.toml` into `deploy/requirements.txt` with hashes via `uv pip compile` |
| `viur env [profile]` | print the resolved profile and the versions of the tools involved |
| `viur project list [profile]` | print the resolved profile |
| `viur script ...` | pull, push and run Scriptor scripts, see below |
| `viur setup-autocomplete [--shell]` | install tab completion for bash, zsh or fish; `autocomplete-info` and `uninstall-autocomplete` go with it |

Every command that reads the configuration takes a profile as its last
positional argument and defaults to `default`.

`viur package <install|update> <admin|vi|scriptor|all>` still works but prints a
deprecation warning and is removed in v3.2. `viur admin install` and its
siblings replace it.

## The project.json

```json
{
    "format": "2.0.0",
    "default": {
        "application_name": "my-app",
        "version": "live-$(year)-$(month)-$(day)",
        "distribution_folder": "./deploy",
        "sources_folder": "./sources",
        "builds": {
            "admin": {
                "kind": "exec",
                "command": "viur admin install",
                "version": "5.0.3"
            },
            "frontend": {
                "kind": "npm",
                "source": "frontend",
                "command": "build"
            }
        },
        "gcloud": {
            "region": "europe-west3",
            "max-instances": "1"
        }
    },
    "develop": {
        "application_name": "my-app-dev",
        "version": "dev-$(user)"
    }
}
```

`format` is the schema version and is maintained by the CLI, which rewrites
older files on load. Everything else lives in profiles: `default` and any number
of named profiles, each of which is `default` overlaid with its own keys.

| Key | Effect |
|---|---|
| `application_name` | the App Engine project id; `viur run` and `viur cloud` act on it |
| `version` | the App Engine version to deploy; placeholders are resolved first, then the result is lowercased and stripped to `a-z`, `0-9` and `-` |
| `distribution_folder` | the folder uploaded to App Engine, default `./deploy` in `viur-base` |
| `sources_folder` | where npm builds find their `source` |
| `builds` | build steps, see below |
| `gcloud.region`, `gcloud.max-instances` | passed to `gcloud app deploy` |
| `gcloud.functions.<name>` | cloud function definitions for `viur cloud deploy cloudfunction`, written by `viur cloud create function` |
| `appyaml` | a file name other than `app.yaml` inside the deploy folder |
| `appyaml_substitition` | `true` replaces `$PROJECT_ID`, `$PROJECT_VERSION` and `$CLI_PROFILE` in `app.yaml` before deploying; an object adds further `"$PATTERN": "value"` pairs |
| `port`, `gunicorn_port` | forwarded to `app_server` by `viur run` |

Note the spelling of `appyaml_substitition`: the key is misspelled in the code
and kept that way so existing files keep working.

### Builds

Each entry under `builds` is one step, run in the order the file lists them. A
step that depends on another one has to come after it.

| Kind | Needs | Does |
|---|---|---|
| `npm` | `source`, `command` | `npm install` and `npm run <command>` in `<sources_folder>/<source>` |
| `exec` | `command` | runs the shell command in the project root |

Two optional keys apply to both kinds: `clean` is a shell command that
`viur build clean` runs after its own cleanup, and `target` overrides the
folder below the deploy folder into which `viur admin|vi|scriptor install`
unpacks a bundle, defaulting to the component name. `version` on a frontend
bundle entry is recorded by the install command and used by `update`.

### Version placeholders

`$(name)` in the `version` string is replaced at deploy time. Available are
every key of the resolved profile plus:

| Placeholder | Value |
|---|---|
| `$(user)` | the OS user running the deploy |
| `$(year)`, `$(month)`, `$(day)` | current date, zero-padded |
| `$(hour)`, `$(minute)`, `$(second)` | current time, zero-padded |
| `$(ref)` | short git SHA of `HEAD` |

Replacement repeats until nothing changes, so a placeholder may expand to
another placeholder.

## Scriptor scripts

`viur script` works against the Scriptor module of a deployed application: it
downloads the scripts stored there, uploads local changes and runs a script
locally with the server's session.

```
viur script configure --url https://my-app.appspot.com --username me
viur script setup             log in and persist the session
viur script pull              server -> working_dir
viur script push --watch      working_dir -> server, re-pushing on file changes
viur script run my_script.py
```

The connection settings and the session live in `viur_scriptor_config.json`
next to `project.json`; the working directory defaults to `scripts/`.

## Development

```
git clone git@github.com:viur-framework/viur-cli.git
cd viur-cli
uv sync
uv run viur --version
```

To try a checkout against a real project, install it there as an editable
dependency:

```
cd your-project
uv add --dev --editable ../viur-cli
```

Pull requests target `develop`; the rules are in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Copyright © 2026 by Mausbrand Informationssysteme GmbH.<br>
Mausbrand and ViUR are registered trademarks of Mausbrand Informationssysteme GmbH.

This project is free software under the MIT license.<br>
Please see the LICENSE file for details.
