#!/usr/bin/env python3
import contextvars
import json
import urllib.parse
import webbrowser
from pathlib import Path
from wsgiref.simple_server import  make_server
from ..cli import scriptor_config
import requests

PORT = 60_000



def callback_app(environ: dict, start_response):
    qs = urllib.parse.parse_qs(environ["QUERY_STRING"])
    callback_app.cookie.set(qs["cookie"][0])
    callback_app.app.set(qs["app"][0])
    start_response("200 OK", [('Content-Type', 'text/plain; charset=utf-8')])
    return [b"This was successful. You can now close this site."]


callback_app.cookie = contextvars.ContextVar("Cookie")
callback_app.app = contextvars.ContextVar("App")


def ensure_login(
    app: str,
    *,
    open_browser: bool = True,
    host: str = None,
) -> bool:


    with make_server('', PORT, callback_app) as httpd:
        sa = httpd.socket.getsockname()
        print("Serving HTTP on", sa[0], "port", sa[1], "...")

        if host is None:
            host = f"https://{app}.appspot.com"
        url = f'{host}/vi/user/get_cookie_for_app?redirect_to=http://localhost:{PORT}'
        if open_browser:
            webbrowser.open(url)
        else:
            print("Open this URL in your browser:")
            print(url)

        httpd.handle_request()  # serve one request, then exit

        cookie_str: str = callback_app.cookie.get()
        key, value = cookie_str.split(";", 1)[0].split("=")
        scriptor_config.get("cookies",{})[key] = value
        scriptor_config.save()

        return True




