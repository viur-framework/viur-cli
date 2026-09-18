---
covers: [viur_cli.build.build, viur_cli.build._build, viur_cli.build._clean]
status: accepted
---
## Seam

A build step is an entry in `default.builds.<name>` of `project.json`
with a `kind`. A new kind is one `case` in `viur_cli.build._build` and one
in `viur_cli.build._clean`. The recognised keys per kind are documented on
those two functions; the config shape is not validated anywhere else.

## Rules

- Every kind gets a `_clean` case, even if it is `pass`. An unknown kind
  aborts the whole `viur build clean` run, not just that entry.
- Generated folders are removed only through `utils.rmdir`. Never call
  `shutil.rmtree` on a path that comes from `project.json`.
- Builds run in JSON declaration order. That order is the only sequencing
  mechanism; there is no dependency graph and none is planned.
- `command` runs through `utils.system` with `shell=True`. `project.json`
  is trusted input; do not put user-supplied strings into a build command.

## Traps

- `target` is relative to `distribution_folder`, `source` is relative to
  `sources_folder`. Two different roots in the same entry.
- `utils.rmdir` refuses paths outside the project root but accepts the
  project root itself. `target: ".."` in an npm build resolves to the root
  and `viur build clean` deletes the project. `package._run_op` guards
  its `target` against this; `_clean` does not (state as of v3.1.1).
- The `admin`, `vi` and `scriptor` entries are ordinary `exec` builds whose
  `command` is `viur package install <x>`, written by `ProjectConfig.migrate`
  and `package.get_version_info`. `viur build release` therefore downloads
  the frontends from GitHub every time. The `version` key on these entries
  is informational (`viur env`); pinning happens only through the version
  inside the command string.
- That written command uses the `viur package` form which the CLI itself
  marks as deprecated for removal in v3.2. Existing `project.json` files
  carry it; removing the shim without a migrate step breaks
  `viur build release`.
- `additional_args` is accepted by `viur build release` and `viur build
  app` and ignored by both kinds.

## Why not

- **Why no `npm run clean`**: not every frontend defines it. The explicit
  `clean` key on the entry is the hook for that; it runs for every kind
  after the kind-specific cleanup.

## See also

- `docs/adr/package.md` for the frontend install entries.
- `docs/adr/utils.md` for the `rmdir` guard.
