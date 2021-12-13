# ViUR cli

Command-line interface for ViUR application maintenance.

## Installation

Use pip or pipenv to install this package

```sh
$ pip install viur-cli
```

## Usage

viur-cli allows you to control, maintain and develop a ViUR project from one central location.

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

## Dependencies

viur-cli depends on

* [click](https://click.palletsprojects.com/)
* [app_server](https://github.com/XeoN-GHMB/app_server)
* [pipfile-requirements](https://github.com/frostming/pipfile-requirements)
* [watchgod](https://github.com/samuelcolvin/watchgod)
* [python-minifier](https://github.com/dflook/python-minifier)

## License

Distributed under the MIT License. See `LICENSE` for more information.
