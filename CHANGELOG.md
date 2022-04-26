# Changelog

This file documents any relevant changes.
## [0.6.17] - 2022-04-26
- chore: fixes some typos

## [0.6.16] - 2022-04-22
- fix: only ask for rebuild requirements if core is not submodule
- feat: added dependency hash and version check for core package

## [0.6.15] - 2022-04-22
- chore: updated app_server to 0.9.0

## [0.6.14] - 2022-04-08
- Updated get_pyodide.py for Pyodide v0.19.1
- Improved release module
  - Only install pyodide when flare apps are configured
  - Some verbose output improvements
  - Some code refactoring
- conf.py holds the default Pyodide version
- Allows to run viur command from anywhere inside the project folder by resolving and chdir'ing backwards
- Improved error reporting and output (fatal error stops program execution)

## [0.6.13] - 2022-03-30
- chore: updated app_server to 0.8.5

## [0.6.12] - 2022-03-30
- chore: updated app_server to 0.8.5

## [0.6.11] - 2022-03-18
- chore: updated app_server to 0.7.4

## [0.6.10] - 2022-03-17
- fix: disabled autoinstall of Autocompletion for bash and zsh

## [0.6.9] - 2022-03-17
- chore: refactored flare.py to use Python standard library tools and pyminifier directly.

## [0.6.8] - 2022-03-09
- chore: updated app_server to 0.7.3

## [0.6.7] - 2022-02-25
- fix: can't use viur with missing project.json

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
