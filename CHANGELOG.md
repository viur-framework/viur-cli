# Changelog

This file documents any relevant changes.

## [2.0.3] 2024-07-29
- fix: breaking typo

## [2.0.2] 2024-07-26
- chore: added support for gcloudfunctions gen2


## [2.0.1] 2024-05-06
- bugfix: removed project.json profile "core" validation throughout the project
- chore: bumped version numbers in setup.cfg
- chore: Added hints to several commands

## [2.0.0] 2024-04-11:
- chore: added deprecation warnings
- feature: Enforcing gcloud tool usage for ViUR Projects
- feature: `viur gcloud init` command
- feature: deployment of gcloud functions
- feature: show logged in gcloud account on `viur run`
- fix: format in project.json
- feature: shows CHANGELOG.md on first start
- feature: added gcloud initiation deployment
- fix: format in project.json
- fix: deployment issues
- chore: added default gcloud account information in env
- chore: update dependencies
- docs: updated documentation and Helptexts
- chore: updated Github workflows
- feature: Appengine Setup can now be done via CLI
- feature: Appengine Roles can now be managed via CLI
- feature: `viur package install` and `viur package update` functions
- refactor: enabled profile support for all viur-cli functions
- fix: `viur env` now runs without errors
- refactor: project.json functionalities
- feature: cloudfunctions creation and deployment via ClI
- feature: backup disabling/ enabling via CLI
- refactor: `viur deploy` is now `viur cloud deploy`

## [1.1.2] 2024-01-26:
- chore: removed python-minifier
- chore: updated appserver

## [1.1.1] 2023-11-28
- chore: updated dependencies
- feat: added npm audit function
 
## [1.1.0] 2023-11-23
- chore: added more `viur2to3` replacements
- fix: fixed `viur script` subdirectory duplicates
- chore: updated Pipenv to work with Python <=3.12
- feat: Added code documentation
- feat: Remove `index.yaml` duplicate entries
- refactor: added update command
- refactor: some PEP8 Changes
- [BREAKING]: Removed all flare scripts and functionality
- [BREAKING]: Removed `scanNPM` function  
- [BREAKING]: Removed `viur init` 


## [1.0.16] 2023-09-29
- feat: Add targets to all install softwares and ensure a specific version is correctly working
- chore: refactored install.py

## [1.0.15] 2023-09-15
- chore: support viur core 3.5.0

## [1.0.14] 2023-09-15
- chore: update app_server to 0.9.6

## [1.0.13] 2023-09-14
- chore: use `viur install admin` to install the vi admin
- chore: update app_server to 0.9.5

## [1.0.11] 2023-07-24
- fix: do_checks now works as expected

## [1.0.10] 2023-07-18
- fix: do_checks now works as expected

## [1.0.9] 2023-07-12
- refactor: local module
- feat: added rmdir method to prevent removing beyond project dir

## [1.0.8] 2023-07-11
- feat: added a clean command to remove build artifacts

## [1.0.7] 2023-07-11
- feat: improved viur3to3 script for core 3.4
- refactor: `viur build` now more generalized

## [1.0.6] 2023-06-28
- fix: viur check:  dont kill the command on error 
- chore: added requests as dependency

## [1.0.5] 2023-06-28
- chore: updated python-minifier to support python 3.11
- feat: added `viur check [--dev]` to do a pipenv check and npm audit. 
- feat: before deployment the cli runs the check command

## [1.0.4] 2023-05-04
- chore: update app_server to 0.9.4
- fix: error wenn updating old project.json formats

## [1.0.3] 2023-04-18
-fix: allow format 1.1.1

## [1.0.2] 2023-04-17
-fix: update project.json to format 1.1.1

## [1.0.1] 2023-04-17
- fix: renamed app kind from `script` to `exec`
- fix: scriptor cli 

## [1.0.0] 2023-04-13
- feat: added `viur build app [NAME]` command which build a specific app
- feat: new app type `script`
- feat: `viur install vi` can now have an optional --target parameter 

## [1.0.0-rc2] 2023-03-31
- fix: renamed `viur script` to `viur tool`
- fix: renamed `viur scriptor` to `viur script`

## [1.0.0-rc1] 2023-03-29
- feat: added `viur install` subcommand to install scriptor and vi
- fix: `viur vi` command is deprecated use `viur install vi` instead
- feat: added `viur scriptor` command to use scriptor scripts
- fix: 2-to-3 script viur 3.3.4 updates
- fix: unified version schema
- feat: added `viur build release` command which build all flare and npm apps
- fix: removed `viur release` command
- feat: apps are now listed in a builds object in the project.json
- feat: 2 app kinds flare and npm are supported
- feat: added `viur project scanNpm` to add existing npm apps
- feat: added `viur script` call different viur related scripts like 2to3, flare or get_pyodide

## [0.7.8] - 2023-03-27
- chore: updated app_server to 0.9.3
- chore: updated click to 8.1.3

## [0.7.7] - 2023-02-17
- fix: broken `viur vi` command

## [0.7.6] - 2023-02-17
- feat: download vi 4 with: `viur vi --next`

## [0.7.5] - 2023-01-20
- fix: 2-to-3 correct some old boneNames
- docu: 2-to-3 documentation added to readme
- feat: 2-to-3 can be applied to a single file

## [0.7.4] - 2022-09-23
- fix: 2-to-3 script was broken 

## [0.7.3] - 2022-09-16
- feat: added 2-to-3 script
- fix: proejctname enforces lowercase

## [0.7.2] - 2022-07-25
- chore: updated app_server to 0.9.2

## [0.7.1] - 2022-07-25
- chore: updated app_server to 0.9.1

## [0.7.0] - 2022-05-20
- feat: index.yaml will be sorted before deployment
- feat: use of `$(variable)` placeholders in version strings, allows to use all
  project configuration values, and additionally for these placeholders:
  - `$(user)` for the username
  - `$(day)` for current date's day
  - `$(month)` for current date's month
  - `$(year)` for current date's year
  - `$(hour)` for current time's hour
  - `$(minute)` for current time's minute
  - `$(second)` for current time's second

## [0.6.19] - 2022-05-18
- fix: requirements regeneration now respects dependency extras with hash

## [0.6.18] - 2022-05-17
- fix: `viur init` and `viur create` working again

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
