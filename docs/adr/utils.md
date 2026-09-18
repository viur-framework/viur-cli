---
covers: [viur_cli.utils.echo_fatal, viur_cli.utils.echo_error, viur_cli.utils.rmdir, viur_cli.utils.system, viur_cli.utils.replace_vars]
status: accepted
---
## Seam

All user-facing output goes through the `echo_*` functions. Aborting the
process is `utils.echo_fatal`, nothing else. Deleting a folder that comes
from configuration is `utils.rmdir`. Running a chained shell string is
`utils.system`; anything new that does not need chaining uses
`subprocess.run` with an argv list directly.

## Rules

- `echo_fatal` is `sys.exit(1)`. Do not call it where a caller could sit
  inside a bare `except:`; that catches `SystemExit` and turns the abort
  into a swallowed error. `except Exception` is safe.
- No new `shell=True` calls outside `utils.system`. It exists for the
  `cd x && npm install && npm run y` chains in the build pipeline; that is
  the only reason.
- `rmdir` is the only way to delete a configured path. Its guard is the
  cwd, which is the project root only after `conf.Config.load` has run.
  Calling it before the config is loaded compares against the user's cwd.

## Traps

- The `rmdir` guard uses `os.path.commonpath` and therefore accepts a
  path equal to the cwd. `rmdir("deploy/..")` from the project root deletes
  the project root. Callers must reject `.`, `..` and paths with
  separators themselves; `package._run_op` does, `build._clean` does not
  (state as of v3.1.1).
- `echo_error` and friends write to **stdout**, in colour. Only the
  deprecation warning in `package.py` uses `err=True`. Tooling that greps
  stderr for viur errors finds nothing.
- `replace_vars` mutates the `vars` dict it is given (adds `user`, `day`,
  `month`, ...). `cloud.deploy` passes a filtered copy of the profile for
  that reason; passing `conf` itself pollutes the profile.
- `$(ref)` is resolved after the fixpoint loop by running `git rev-parse`
  in the cwd. Outside a git checkout this raises `CalledProcessError`
  instead of a fatal message.
- `system()` exits the whole CLI on a non-zero return. A build step that
  legitimately returns non-zero cannot be marked as "allowed to fail".

## Why not

- **Why `click.echo` wrappers instead of `logging`**: coloured
  one-line CLI output, no levels, no handlers. Adding `logging` would give
  two output paths for the same message.

## See also

- `docs/adr/build.md` for the callers of `rmdir` and `system`.
- `docs/adr/conf.md` for the `chdir` that the `rmdir` guard depends on.
