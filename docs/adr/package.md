---
covers: [viur_cli.package.package, viur_cli.package._run_op, viur_cli.package.get_version_info, viur_cli.package.REPOS]
status: accepted
---
## Seam

A downloadable frontend component needs three things, all in
`package.py`: an entry in `REPOS` (GitHub repo and release asset name), a
handler in the `handlers` dict inside `viur_cli.package._run_op`, and a
click group `viur <component>` with `install` and `update` that call
`_run_op`. Missing one of the three means the `all` path skips the
component silently.

## Rules

- Every install goes through `_run_op`. It owns the `builds.<comp>.target`
  guard (plain folder name only, because the target ends in
  `shutil.rmtree`). Never call an `_install_*` function directly.
- `get_version_info` is not a lookup. On success it creates or updates
  `default.builds.<comp>` in `project.json` and saves. Do not call it to
  "just check" a version.
- `viur package ...` is a compatibility shim for v3.2 removal. New
  behaviour goes into the `viur <component>` groups, not into `package`.

## Traps

- `all` means different sets per operation: on `install` it is `admin` +
  `scriptor` (never `vi`), on `update` it is whatever is in the profile's
  `builds`.
- `REPOS["admin"]` and `REPOS["vi"]` both name the asset `viur-vi.zip`.
  That is not a copy-paste error: the `vi-admin` releases publish their
  asset under that name (checked against the GitHub API, 2026-09-18).
- `_install_scriptor` extracts the zip into the cwd, `_install_admin` and
  `_install_vi` extract into the target path. The zips have different
  layouts; check the archive before unifying the three functions.
- Version resolution uses `requests` against the unauthenticated GitHub
  API (60 requests per hour). On failure the download URL is built from
  the unvalidated version string and the install proceeds.
- The command string written into `project.json` carries the version only
  for explicit installs. `install <comp>` without a version writes
  `viur package install <comp>`, which resolves to `latest` on every
  future `viur build release`.

## Why not

- **Why a shared `_run_op` behind both the deprecated and the new
  command surface**: the deprecation is a rename, not a behaviour change.
  Two code paths would drift before v3.2.

## See also

- `docs/adr/build.md` for what the written `builds` entries do at build
  time.
- `docs/adr/utils.md` for `rmdir`.
