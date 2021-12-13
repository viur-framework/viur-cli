import click


def echo_error(msg):
    """colored cli feedback"""
    click.echo(click.style(msg, fg="red"))


def echo_info(msg):
    """colored cli feedback"""
    click.echo(click.style(msg, fg="cyan"))
