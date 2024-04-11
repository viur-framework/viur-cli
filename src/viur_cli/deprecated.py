import click
from . import cli, echo_error

'''
    This Document keeps Track of "Deprecation Warnings"
'''

@cli.command(hidden= True)
@click.argument('argument', nargs=-1)
def install(argument: list):
    echo_error("the ViUR install command is out of Date")
    echo_error("Please use the 'viur package' commands instead")

@cli.command(hidden= True)
@click.argument('argument', nargs=-1)
def deploy(argument: list):
    echo_error("The 'deploy' command out of Date")
    echo_error("Please use 'viur cloud deploy' commands instead")
