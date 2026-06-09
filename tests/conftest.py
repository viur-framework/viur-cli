"""Gemeinsame Test-Fixtures.

``viur_cli.conf`` legt beim Import einen globalen ``ProjectConfig()``-Singleton an,
der den Verzeichnisbaum nach ``project.json`` absucht und dabei ``os.chdir`` bis zur
Wurzel ausführt (im viur-cli-Repo selbst gibt es keine ``project.json``). Damit
dieser Import-Seiteneffekt nicht das Arbeitsverzeichnis nachfolgender Tests
verschiebt, stellt die autouse-Fixture vor und nach jedem Test das ursprüngliche
cwd wieder her.
"""

import os

import pytest

_ORIG_CWD = os.getcwd()


@pytest.fixture(autouse=True)
def _restore_cwd():
    os.chdir(_ORIG_CWD)
    yield
    os.chdir(_ORIG_CWD)
