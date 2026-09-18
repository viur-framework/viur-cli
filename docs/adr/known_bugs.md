---
covers: [viur_cli.utils.rmdir, viur_cli.build._clean, viur_cli.package.get_version_info, viur_cli.package._install_scriptor, viur_cli.package.checkreturncode, viur_cli.cli.cli, viur_cli.cloud.datastore_export, viur_cli.cloud.deploy, viur_cli.local.env, viur_cli.local.run, viur_cli.conf.Config, viur_cli.scriptor.login.ensure_login]
status: proposed
---
## Traps

Defects found while writing the seam documentation, state as of v3.1.1
(2026-09-18). Each item was read in the source; "verified" means it was
also reproduced. Nothing here is fixed. Remove an entry with the fix.

**Data loss**

- `utils.rmdir` accepts a path equal to the cwd (`os.path.commonpath`
  returns the cwd for `deploy/..`). An npm build with `target: ".."`
  makes `viur build clean` delete the project root. `build._clean` has
  no plain-name guard; `package._run_op` has one. Verified with a
  scratch directory.

**Crashes**

- `cloud.datastore_export` calls `datetime.now()` but `cloud.py` never
  imports `datetime`. `viur cloud copy local2bucket` dies with
  `NameError` after the bucket prompt.
- `cloud.deploy`, branch `elif app_yaml.name != "app.yaml"`: uses
  `app_yaml_tmp.resolve()` while `app_yaml_tmp` is `None`. A custom
  `appyaml` without substitution raises `AttributeError`. Should be
  `app_yaml.resolve()`. (Also in the local TODO.)
- `cli.cli` runs `subprocess.check_output(["uv", "self", "version"])`
  unguarded. Without `uv` on `PATH` every invocation, including
  `viur --help`, ends in a `FileNotFoundError` traceback. If the output
  has no `x.y.z`, `match.group(1)` raises `AttributeError`.
- `local.env` prints `conf['builds'][entry]['version']` for every build.
  npm builds have no `version` key, so the whole "Project Info" block
  aborts with a `KeyError` that is caught and printed as
  "Error while collecting viur info". The `if entry in conf["builds"]`
  inside the loop is always true.
- `scriptor.login.ensure_login` binds port 60000 with no fallback and no
  error handling. A busy port gives an `OSError` traceback.

**Wrong behaviour**

- `package.get_version_info` checks
  `config["default"]["builds"].get("version")` instead of
  `builds[software].get("version")`. The condition is always true, so
  every version lookup rewrites `project.json`.
- `package.get_version_info` and `conf.ProjectConfig.migrate` write
  `"command": "viur package install <x>"` into `project.json`, the form
  the CLI marks as deprecated for removal in v3.2. Needs a migrate step
  to the `viur <x> install` form before the shim goes. (Also in the
  local TODO.)
- `cloud.deploy` reads the config key `appyaml_substitition`
  (misspelled). The README documents this spelling; renaming needs a
  migrate step plus alias. (Also in the local TODO.)
- `package._install_scriptor`: the progress labels test `step == 1`
  twice, so step 3 has no label and steps 2 and 3 show the wrong text.
  The final message says "Installed admin". The zip is extracted with
  `extractall()` into the cwd while the cleanup step removes
  `dist/<target>`; whether the archive carries its own top-level folder
  is unverified. If it does not, the install lands in the project root.
- `local.run` wraps `get_user_info()` in a bare `except:`, which also
  swallows `KeyboardInterrupt` and reports it as a login problem.

**Dead or sloppy code**

- `package.checkreturncode` has no callers.
- `build._clean`: `if build_cfg["kind"] == "npm"` inside `case "npm"`
  is always true.
- `conf.Config.load` opens `FILENAME` without closing it.
- `conf.ProjectConfig.migrate` validates the format version with
  `assert`, which `python -O` strips.
- `conf.Config.load` detects the filesystem root with
  `os.getcwd() == "/"`. On Windows that never matches; the walk-up loop
  would not terminate. Unverified, no Windows box.
- `package.get_version_info` indexes `version[0]` and raises
  `IndexError` on an empty version string.
- The temporary zip files in `_install_admin`, `_install_vi` and
  `_install_scriptor` are downloaded with `urlretrieve` (no timeout) into
  the cwd and are not removed when a step raises.

## See also

- `docs/adr/utils.md` and `docs/adr/build.md` for the `rmdir` guard.
- `docs/adr/package.md` for the `get_version_info` side effect.
