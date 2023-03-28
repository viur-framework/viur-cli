"""
Dialogs API.

This module provides several dialogs to be used for several user-interactions.

- alert: Show a modal message to be confirmed
- confirm: Show a Yes-No or Yes-No-Cancel dialog
- input: Input dialog with various types
- select: Select choice of several options, with multi-selection option.
"""

from .utils import is_pyodide_context

if is_pyodide_context():
    import js, pyodide
    from js import self as _self
    import manager
else:
    import asyncio
    import click

import time
import datetime
import math


async def wait():
    if is_pyodide_context():
        while manager.resultValue is None:
            await manager.sleep(250)
    else:
        await asyncio.sleep(250)


async def alert(text: str):
    """
    Provide a message and stop program execution until accepted.
    """
    if is_pyodide_context():
        _self.postMessage(type="alert", text=text)
        await wait()
        manager.reset()
        manager.resultValue = None
    else:
        click.pause("Press any key to continue")


async def confirm(text: str, *, title: str = "Confirm", allow_cancel: bool = False) -> bool | None:
    """
    Provide a Yes-No or Yes-No-Cancel-dialog.
    """
    if is_pyodide_context():
        _self.postMessage(type="confirm", title=title, text=text, cancel=allow_cancel)
        await wait()
        ret = manager.copyResult()
        manager.reset()
        manager.resultValue = None

        if ret < 0:
            return None
        elif ret == 0:
            return False

        ret = True

    else:
        ret = click.confirm(text, abort=allow_cancel)

    return ret


async def input(text: str, *, title: str = "Input", type: str = "input", use_time: bool = False, empty: bool = False):
    """
    Provide a dialog asking for some value.
    """

    if is_pyodide_context():
        _self.postMessage(type="input", title=title, text=text, input_type=type, use_time=use_time, empty=empty)
        await wait()
        tmp = manager.copyResult()
        manager.reset()
        manager.resultValue = None

        if type == "date":
            js.console.error(tmp)
            return datetime.datetime.fromtimestamp(math.floor(tmp / 1000.0))

        return tmp
    else:
        # click.echo(title)  # not required
        ret = click.prompt(text)
        if type == "date":
            def validate_date(date_text):
                try:
                    return datetime.date.fromisoformat(date_text)
                except ValueError:
                    click.echo("Incorrect data format, should be YYYY-MM-DD")

                return None

            def validate_datetime(date_text):
                try:
                    return datetime.datetime.fromisoformat(date_text)
                except ValueError:
                    click.echo("Incorrect data format, should be YYYY-MM-DD HH:MM:SS")

                return None

            if use_time:
                while not validate_date(ret):
                    ret = click.prompt(text)
            else:
                while not validate_datetime(ret):
                    ret = click.prompt(text)

            return ret
        elif type == "number":
            def check_number(value: str):
                try:
                    r = float(value.replace("," "."))
                    return ret
                except:
                    try:
                        r = int(value)
                        return r
                    except:
                        return None
                return None

            while True:
                ret = check_number(ret)
                if ret is None:
                    click.echo("Enter a valid number.")
                    ret = click.prompt(text)
                else:
                    break

            return ret
        else:
            return ret


async def input_date(*args, **kwargs):
    kwargs |= {"type": "date"}
    return await input(*args, **kwargs)


async def input_number(*args, **kwargs):
    kwargs |= {"type": "number"}
    return await input(*args, **kwargs)


async def input_string(*args, **kwargs):
    kwargs |= {"type": "string"}
    return await input(*args, **kwargs)


async def input_text(*args, **kwargs):
    kwargs |= {"type": "text"}
    return await input(*args, **kwargs)


input.date = input_date
input.number = input_number
input.text = input_text
input.string = input_string


async def select(text: str, choices: tuple[str] | list[str] | dict[str, str], *,
                 title: str = "Select", multiple: bool = False):
    if isinstance(choices, (list, tuple)):
        choices = {str(k): str(k) for k in choices}

    if not isinstance(choices, dict):
        raise ValueError("'choices' must be either a list or a dict.")

    # Browser-mode
    if is_pyodide_context():
        choices = pyodide.ffi.to_js(choices, dict_converter=js.Object.fromEntries)

        _self.postMessage(type="select", title=title, text=text, choices=choices, multiple=multiple)
        await wait()

        ret = manager.resultValue
        if multiple:
            ret = ret.to_py()

        manager.reset()
        manager.resultValue = None

        return ret

    # CLI-mode
    maxkey = max([len(k) for k in choices])
    menu = [f"{k: <{maxkey}} - {v}" if k != v else str(v) for k, v in choices.items()]

    if not multiple:
        ret = click.prompt(
            "\n".join(menu) + "\n" + text,
            type=click.Choice(list(choices.keys()))
        )
    else:
        options = list(choices.keys())

        while True:
            ret = click.prompt("\n".join(menu) + "\n" + text + f" ({', '.join(options)})", type=str)
            ret = [c.strip() for c in ret.split(",")]
            if all([v in options for v in ret]):
                break

            click.echo(f"Invalid input entered. Allowed values: {options}")

    return ret
