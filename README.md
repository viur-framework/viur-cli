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
$ viur-cli --help
$ viur-cli init
$ viur-cli run
$ viur-cli deploy
$ viur-cli index
$ viur-cli vi
$ viur-cli flare vi watch
$ viur-cli env
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
