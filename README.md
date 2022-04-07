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
