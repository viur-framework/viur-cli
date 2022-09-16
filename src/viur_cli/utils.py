import click, sys, typing, datetime, getpass


def echo_error(msg):
    """colored cli feedback"""
    click.echo(click.style("ERROR: " + msg, fg="red"))


def echo_fatal(msg):
    echo_error(msg)
    sys.exit(1)


def echo_info(msg):
    """colored cli feedback"""
    click.echo(click.style(msg, fg="cyan"))


def replace_vars(string: str, vars: typing.Optional[typing.Dict[str, str]] = None) -> str:
    """Replaces $(placeholders) in a string by values from a dict until no more values are being replaced.

    The function enriches the provided vars dictionary by the following defaults if not given:
    - user: Current user's name
    - day: Current date's day
    - month: Current date's month
    - year: Current date's year
    - hour: Current date's hour
    - minute: Current date's minute
    - second: Current date's second
    """
    # set some defaults
    if vars is None:
        vars = {}

    # current user
    if "user" not in vars:
        try:
            whoami = getpass.getuser()
        except:
            whoami = "viur"

        vars["user"] = whoami

    # date values
    now = datetime.datetime.now()
    for item in ["day", "month", "year", "hour", "minute", "second"]:
        if item not in vars:
            vars[item] = "%02d" % getattr(now, item)

    # replaces variables until string doesn't change anymore.
    old_string = ""

    while old_string != string:
        old_string = string
        for var, content in vars.items():
            string = string.replace(f"$({var})", str(content))

    return string
