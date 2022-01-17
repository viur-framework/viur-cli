import click


def echo_error(msg: str):
    """colored cli feedback"""
    click.echo(click.style(msg, fg="red"))


def echo_info(msg: str):
    """colored cli feedback"""
    click.echo(click.style(msg, fg="cyan"))
