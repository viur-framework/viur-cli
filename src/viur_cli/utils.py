import click, sys


def echo_error(msg):
    """colored cli feedback"""
    click.echo(click.style("ERROR: " + msg, fg="red"))


def echo_fatal(msg):
    echo_error(msg)
    sys.exit(1)


def echo_info(msg):
    """colored cli feedback"""
    click.echo(click.style(msg, fg="cyan"))
