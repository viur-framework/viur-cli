import setuptools
import os
from subprocess import call
from setuptools.command.install import install
from setuptools.command.develop import develop




class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
        call(['./postinstall.sh'])

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        call(['./postinstall.sh'])


setuptools.setup()
