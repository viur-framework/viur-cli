## ViUR-ClI

The ViUR-Cli project allows the control of ViUR projects from one central location.

### Installation

use pip or pipenv to install this package

 ```sh
    pip install viur-cli
   ```

### Some Examples

 ```sh 
 viur-cli --help
 viur-cli init
 viur-cli run
 viur-cli deploy
 viur-cli index
 viur-cli vi
 viur-cli flare vi watch
 viur-cli env
 ```

### Dependencies

The app server dependents on the following packages

* [click](https://click.palletsprojects.com/)
* [app_server](https://github.com/XeoN-GHMB/app_server)
* [pipfile-requirements](https://github.com/frostming/pipfile-requirements)
* [watchgod](https://github.com/samuelcolvin/watchgod)
* [python-minifier](https://github.com/dflook/python-minifier)

## License

Distributed under the MIT License. See `LICENSE` for more information.
