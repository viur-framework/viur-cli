# ViUR-cli

Command-line interface for ViUR application development maintenance.

## Usage

viur-cli allows for control, maintain and develop a ViUR project from one central location by using the `viur` command
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

To use viur-cli in your ViUR projects, use [pipenv](https://pypi.org/project/pipenv/).

```bash
$ pipenv install --dev viur-cli
```

## Packaged scripts

In order to use some of the packaged scripts, it is possible to simply run them from the environment that you installed viur-cli into. So if you are using a pipenv, then the scripts will be available in the shell just like you would run viur-cli by calling viur as well.

A handy script that has to be started this way is viur-2to3, which will automatically crawl through a project folder and detect deprecated syntax. 
It is not only useful for porting viur2 projects to viur3, but also when there are deprecations or breaking changes in viur3!
You should start it like this in your project folder:

```sh
$ viur-2to3 -d .
```

This will dry-run the script in the current directory and not make any changes, only suggestions. If you want to make the changes, leave out the -d argument and if you are a daring go-getter and like to live dangerously, replace the -d with -x, which will write the suggested changes without making a backup of the changed files.

## Development

If you want to hack viur-cli, clone viur-cli next to your viur project folder.

```sh
$ git clone git@github.com:viur-framework/viur-cli.git
$ ls -1
viur-cli
your-project
```

Then, add it to your project this way

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

Distributed under the MIT License. See `LICENSE` for more information.
