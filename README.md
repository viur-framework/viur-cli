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

## What does it do?
`viur-cli` allows to control, maintain and develop a ViUR project from one central location by using the `viur` command.


## Installation

To use `viur-cli` in your ViUR projects, install the [PyPI package `viur-cli`](https://pypi.org/project/pipenv/).

```bash
$ pipenv install --dev viur-cli
```

## Usage

```sh
$ viur --help
```
will show all the commands that are currently supported by viur-cli

```sh
$ viur create myapp
```
this will create a new project folder, clone the base project and then call `viur init` to prepare a project.json
you can use this to get started quickly with a new viur project from scratch.

```sh
$ viur init
```
this will initialize a new project in the current folder, you will be asked a couple of questions like if 
you would like to create a new project.json file, what components should be preinstalled and what the 
projectID of your application will be.

```sh
$ viur run [target]
```
run the appserver and start your app locally. You may specify a target projectID.

```sh
$ viur check {npm|--dev|--autofix}
```
Runs a security check for the python environment and for each npm project registered under builds.

```sh
$ viur enable {backup}
```
create a backup bucket and enable the gcloud service worker account to access it.


```sh
$ viur package {install|update} {vi|scriptor|admin|all} 
```
handles ViUR ecosystem package operations

Commands:
- `install`  installs a ViUR package (in a specific version)
- `update`   updates a ViUR package to the newest version

Arguments:
- `profile`  profile to install to
- `version`  version to install

```sh
$ viur build release
```
build all npm apps and produce a release that can be deployed

```sh
$ viur build app [appname]
```
build a specific app

```sh
$ viur cloud deploy {app|index|cloudfunction} {profile} {--ext|--yes|--name}
```
This Function deploys the Google Cloud application and / or different .yaml files
Scripts:
- `app`           Deploy application to the Google Appengine
- `index`         Deploy index.yaml to Google Appenginge
- `cloudfunction` Deploy Cloudfunction to Google Appengine
Commands:
- `profile`       The project.json profile you want to Work from


```sh
$ viur cloud {enable|disable} backup
```
Enable/ Disable the Backup buckets you need to Backup a cloud project in the Google Cloud Console

```sh
$ viur cloud setup {gcloud|gcroles} 
```
Scripts:
- `gcloud`    This Function setups your project to work on the gcloud plattform
- `gcroles`   This function lets you set up Roles for your google appengine Workspace


```sh
$ viur cloud get {gcroles} 
```
Scripts:
- `gcroles`   This function lets you get Roles for your google appengine Workspace in a readable .json Format


```sh
$ viur env
```
check the environment you are in right now, show versions of viur-cli, viur-core and vi etc.

```sh
$ viur project {add|remove|list}
```
with this you can manage your project.json or generate a new one. You can add or remove targets to/from the 
project.json, list what has been added to the project.json, to be built when running `viur build release`.

```sh
$ viur update {requirements}
```
with this you can update your project specific requirements.txt file automatically

## The project.json
The `project.json` is your core project configuration file for every viur related operation.
It contains the default viur project profile and it can be expanded with several individual project profiles.

### Example project.json
```json lines
{
    /* 
      The format Key, Value pair defines the project json format, the viur-cli uses
    */
    "format": "2.0.0",
    /*
      The first level contains of your profiles
      "default" is a profile, which is inherited by "develop" and "live" and can be customized for particular versions 
      and/or GAE projects. Therefore, every profile can contain all keys from the "default" profile.*/
    "default": {
        /*
          The builds level declares steps for the `viur build` command.
          It can contain viur components and other components that need to be build before project deployment
        */
        "builds": { 
            "admin": {
                "command": "viur install admin",
                "kind": "exec",
                "version": "4.0.8"
            },
            "npm": {
                "command": "build",
                "kind": "npm",
                "source": ""
            }
        },
        "core": "3.5.1",  // viur-core version of your project
        "distribution_folder": "./deploy", // Deploy folder uploaded to GAE
        "sources_folder": "./sources",
        "version": "live-$(year)-$(month)-$(day)", // Version string; Variables can be used here.
        "application_name": "my-live-app-viur3" // Name of the GAE project *4
    },
    "develop": {  
        "application_name": "my-dev-app-viur3", 
        "version": "dev-$(user)"  
    }
}

```

## Viur scripting interface

There is a new core component that enables us to pull and push python scripts from/to a deployed application and run these in a sandbox or even locally.
The GUI version is called scriptor and can be accessed via a webinterface, but viur-cli also has a cli for this:

```sh
$ viur script {configure|pull|push|run|setup}
```
Commands:
- `configure`  Manage configuration settings.
- `pull`       Pull contents from server to working_dir.
- `push`       Push contents of working_dir to server.
- `run`        Locally run a script located in the working_dir.
- `setup`      Setup user session with a given username and...


## Packaged tools

In order to use the packaged tools, you can run:

```sh
$ viur tool {2to3|pyodide|ssl-fix}
```
Scripts:
- `2to3`     viur porting script
- `pyodide`  run the get_pyodide command
- `ssl-fix`  ssl fix for MacOS

for example the 2to3 script helps porting viur2 project to viur3, it can be used to automatically rename some things that are deprecated 
in viur3 as well, so you can use it whenever a new core version is released for viur3 projects as well:

```sh
$ viur tool 2to3 -d .
```
will dry-run the script in the current directory and not make any changes, only suggestions. If you want to make the changes, 
leave out the -d argument and if you are a daring go-getter and like to live dangerously, replace the -d with -x, 
which will write the suggested changes without making a backup of the changed files.

## Development

If you want to hack `viur-cli`, clone this repository next to the folder of your ViUR project.

```sh
$ git clone git@github.com:viur-framework/viur-cli.git
$ ls -1
viur-cli
your-project
```

Then, add it to your project as an editable dependency using

```sh
$ cd your-project
$ pipenv install --dev --editable ../viur-cli
```

## Dependencies

viur-cli depends on

* [click](https://click.palletsprojects.com/)
* [app_server](https://github.com/XeoN-GHMB/app_server)
* [pipfile-requirements](https://github.com/frostming/pipfile-requirements)
* [watchgod](https://github.com/samuelcolvin/watchgod)
* [python-minifier](https://github.com/dflook/python-minifier)

## License

Copyright © 2024 by Mausbrand Informationssysteme GmbH.<br>
Mausbrand and ViUR are registered trademarks of Mausbrand Informationssysteme GmbH.

This project is free software under the MIT license.<br>
Please see the LICENSE file for details.
