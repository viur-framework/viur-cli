# Changelog

This file documents any relevant changes.
## [0.6.6] - 2022-02-23
- [BREAKING]: `viur release` requires pyenv to enforce python 3.9.5

## [0.6.5] - 2022-02-22
- added: config format versioning
- added: pyodide version
- added: conf update function
- added: npm command by default it tries to call npm run build
- added: release command
- [BREAKING]: vue command removed, use npm instead
- [BREAKING]: assets command removed, use npm instead
- 
## [0.6.4] - 2022-02-21
- fix: get-pyodide now uses 0.19

## [0.6.3] - 2022-01-21
- feat: Updated python-minifier to allow Python 3.10

## [0.6.2] - 2022-01-21
- feat: Autocompletion for bash and zsh

## [0.6.1] - 2021-12-21

- fix: `viur init` with no project.json

## [0.6.0] - 2021-12-15

- feat: `viur assets [init | build]`
- feat: `viur vue [add | remove | serve | build]`
- fix: show help if called wihout parameter
- feat: collect core and vi version if not used as submodule
- feat: optimized vi update handler
- fix: block flare release if zip command is missing on System
- chore: updated flare and get-pyodide scripts
- feat: added git verison to env overview
- feat: on init we now can add vi as submodule to project

## [0.5.5] - 2021-12-13

- [BREAKING]: `viur-cli` is now `viur`
- [BREAKING]: `viur-cli deploy` is now `viur deploy app`
- [BREAKING]: `viur-cli index` is now `viur deploy index`
- [BREAKING]: `viur-cli flare [appname] [release | debug | watch]` is
  now `viur flare [release | debug | watch] [appname]`
- feat: `viur create [projectname]`
- feat: `viur project [add | remove | list | addFlare]`

## [0.5.1] - 2021-12-03

- fix: flare apps buildscripts

## [0.5.0] - 2021-11-08

- first release
