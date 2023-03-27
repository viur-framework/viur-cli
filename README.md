<div align="center">
    <img src="https://github.com/viur-framework/viur-artwork/raw/main/icons/icon-cli.svg" height="196" alt="A hexagonal logo of the viur-cli" title="viur-cli">
    <h1>viur-cli</h1>
    <a href="https://pypi.org/project/viur-cli/">
        <img alt="Badge showing current PyPI version" title="PyPI" src="https://img.shields.io/pypi/v/viur-cli">
    </a>
    <a href="LICENSE">
        <img src="https://img.shields.io/pypi/l/viur-cli" alt="Badge displaying the license" title="License badge">
    </a>
    <br>
    Command-line interface for <a href="https://www.viur.dev">ViUR framework</a> project maintenance.
</div>

## Usage

`viur-cli` allows to control, maintain and develop a ViUR project from one central location by using the `viur` command.

```sh
$ viur --help
$ viur init
$ viur create myapp
$ viur run
$ viur deploy app
$ viur deploy index
$ viur vi
$ viur flare watch vi
$ viur env
```

## Installation

To use `viur-cli` in your ViUR projects, install the [PyPI package `viur-cli`](https://pypi.org/project/pipenv/).

```bash
$ pipenv install --dev viur-cli
```

## Packaged scripts

In order to use the packaged scripts, it is possible to simply run them from the environment that you installed viur-cli into.
So if you are using a pipenv, then the scripts will be available in the shell just like you would run viur-cli by calling viur as well.

A handy script that has to be started this way is viur-2to3, which will automatically crawl through a project folder and detect deprecated syntax. 
It is not only useful for porting viur2 projects to viur3, but also when there are deprecations or breaking changes in viur3!
You should start it like this in your project folder:

```sh
$ viur-2to3 -d .
```

This will dry-run the script in the current directory and not make any changes, only suggestions. If you want to make the changes, leave out the -d argument and if you are a daring go-getter and like to live dangerously, replace the -d with -x, which will write the suggested changes without making a backup of the changed files.

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

Copyright © 2023 by Mausbrand Informationssysteme GmbH.<br>
Mausbrand and ViUR are registered trademarks of Mausbrand Informationssysteme GmbH.

This project is free software under the MIT license.<br>
Please see the LICENSE file for details.
