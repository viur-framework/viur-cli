---
covers: [viur_cli.conf.Config, viur_cli.conf.ProjectConfig, viur_cli.conf.ScriptorConfig, viur_cli.conf.print_changelog_from_github]
status: accepted
---
## Seam

A new on-disk config file is a subclass of `viur_cli.conf.Config` with
`FILENAME` and `VERSION` set and `migrate()` overridden. Nothing else.

Commands never build their own instance. They use the module globals
`viur_cli.conf.config` (project.json) and `viur_cli.conf.scriptor_config`
and call `config.get_profile(profile)` inside the command body.

Schema changes to `project.json` go into `ProjectConfig.migrate()` as a
new `if self["format"] == "<old>"` block plus a bump of `VERSION` and of
the allowed-format list in the `assert`.

## Rules

- No second `ProjectConfig()` anywhere. `load()` runs `os.chdir` and
  `migrate()` again, and `migrate()` may prompt interactively, call the
  GitHub releases API and rewrite `project.json`.
- `config` may be `None`. The module swallows the `SystemExit` from the
  auto-load so `viur --help`, shell completion and the mkdocs shim work
  outside a project. Never touch `config` at module import time in a
  command module; fail inside the command via `get_profile`.
- `migrate()` must be idempotent. It runs on every CLI invocation, not only
  after an upgrade, and always ends in `save()`.
- Renaming a `project.json` key needs a migrate step. The misspelled key
  `appyaml_substitition` (read by `cloud.deploy`) stays until one exists.
- Profile names `format` and `default` are reserved. `default` is the base
  layer every profile is merged onto.

## Traps

- `load()` changes the process cwd to the project root and every command
  relies on it: relative paths in `project.json` are relative to the
  project root, not to where the user typed `viur`. Do not "fix" a path
  bug by resolving against the user's cwd.
- `get_profile()` is a shallow merge (`default.copy() | self[profile]`).
  A profile that defines its own `builds` replaces the whole `builds` dict
  of `default`; nested keys are not merged.
- Passing `path=` to the constructor turns "file not found at filesystem
  root" into "create the file at `path`". `ScriptorConfig(path=config.path)`
  uses this; `ProjectConfig()` never does and aborts instead.
- `ScriptorConfig` is discovered by the same walk-up as `project.json`. A
  `viur_scriptor_config.json` in a parent directory shadows the project's.
- `cli-version` in `project.json` is compared to the running CLI version on
  every run. A mismatch triggers a network call for release notes and a
  save. Offline this only prints an error and continues.
- `self["format"]` is set before `load()` and overwritten by the file
  content; the `assert` list is the only validation.

## Why not

- **Why a `dict` subclass and not a dataclass**: deferred on purpose (see
  the comment at the bottom of `conf.py`). A dataclass next to the dict
  globals would double the migration surface. Replace it in one step or
  not at all.
- **Why swallow `SystemExit` at import**: the alternative (lazy loading)
  touches every command. Until that lands the guard stays; removing it
  breaks `viur --help` outside a project.
- **Why `migrate()` saves every time**: a format upgrade must persist
  before the command runs. The cost is that `project.json` is rewritten
  and re-indented on every invocation. Accepted.

## See also

- `docs/adr/cli.md` for how command modules get hold of `config`.
- `docs/adr/build.md` for the `builds` section that `migrate()` rewrites.
