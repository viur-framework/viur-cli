import click
import json
import requests
import os
import re
import importlib
import hashlib
import asyncio
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import scriptor as scriptor_lib
import glob
import tempfile
import sys

import importlib.util
from scriptor import Request, init, viur
from requests.sessions import cookiejar_from_dict
from getpass import getpass
from urllib.parse import urlencode
from weakref import proxy

from ..cli import cli



class Config(dict):
    CONFIG_FILE_NAME = "scriptor_config.json"

    def __new__(cls):
        try:
            cls._instance
        except AttributeError:
            cls._instance = None

        if not cls._instance:
            cls._instance = super().__new__(cls)
            if os.path.exists(cls.CONFIG_FILE_NAME):
                with open(cls.CONFIG_FILE_NAME, "r") as f:
                    for k, v in json.load(f).items():
                        cls._instance[k] = v

        return proxy(cls._instance)

    def dump(self):
        with open(self.CONFIG_FILE_NAME, "w") as f:
            json.dump(self, f)

    def __setitem__(self, __key: str, __value: object) -> None:
        super().__setitem__(__key, __value)
        self.dump()

    def __delitem__(self, __key: str) -> None:
        super().__delitem__(__key)
        self.dump()


DEFAULT_BASE_URL = "http://localhost:8080"
DEFAULT_WORKING_DIR = "scriptor_files/"


@cli.group()
def scriptor():
    pass


@scriptor.command()
@click.option('--url', default=None, help='Setting the url')
@click.option('--username', default=None, help='Setting the username')
@click.option('--working_dir', default=None, help='Setting the working directory')
def configure(url: str, username: str, working_dir: str):
    if url:
        Config()["base_url"] = url

    if username:
        Config()["username"] = username

    if working_dir:
        Config()["working_dir"] = working_dir.replace("\\", "/")


@scriptor.command()
def setup():
    config = Config()
    base_url = config.get("base_url", DEFAULT_BASE_URL)
    try:
        session = requests.session()
        skey = session.get(base_url + "/json/skey")
        username: str = config.get("username", "")
        if not username:
            username = click.prompt("Enter the username")

        password: str = click.prompt("Enter the password", hide_input=True)

        response = session.post(base_url + "/vi/user/auth_userpassword/login", data={
            "skey": skey.json(),
            "name": username,
            "password": password
        })

        if response.text != "FAILURE":
            config["cookies"] = session.cookies.get_dict()
            click.echo("Scriptor-cli setup was successfully.")
        else:
            if "cookies" in config:
                del config["cookies"]
            click.echo("Failed to login. Did you maybe entered the wrong password?")
    except KeyboardInterrupt:
        pass
    except:
        click.echo("Failed to setup scriptor cli.")


@scriptor.group()
@click.pass_context
def command(ctx: click.Context):
    base_url = Config().get("base_url", DEFAULT_BASE_URL)

    s = requests.Session()
    s.cookies = cookiejar_from_dict(Config().get("cookies", {}))

    response = s.get(base_url+"/vi/user/view/self", cookies=Config().get("cookies", {}))
    if not response.ok:
        click.echo("Invalid account session, go to setup again...")
        ctx.invoke(setup)
        ctx.close()


def build_url(url: str):
    return Config()["base_url"] + "/" + url


viur.request.build_url = staticmethod(build_url)


@command.command()
@click.option('--force', default=False, help='Replacing the files with the new (force)')
def pull(force: bool):
    Request.COOKIES = cookiejar_from_dict(Config().get("cookies", {}))
    from scriptor.module import TreeModule
    tree = TreeModule("script")

    async def main():
        try:
            await tree.structure("node")
        except:
            click.echo("Failed to pull... Is the script module included?")
            return

        working_dir = Config().get("WORKING_DIR", DEFAULT_WORKING_DIR)
        if working_dir:
            async def for_each(group: str, entry: object):
                _path = os.path.join(working_dir, entry["path"])

                if group == "node":
                    if not os.path.exists(_path):
                        os.makedirs(_path)
                else:
                    def create_file():
                        with open(_path, "a+") as f:
                            f.write(entry["script"])

                    if os.path.exists(_path):
                        if force:
                            os.remove(_path)
                            create_file()
                        else:
                            with open(_path, "r") as f:
                                online_content = entry["script"].replace("\r", "").encode("utf-8")
                                file_content = f.read().replace("\r", "").encode("utf-8")
                                if hashlib.sha256(online_content).digest() != hashlib.sha256(file_content).digest():
                                    if click.confirm(f"There is a difference of this file: {entry['path']}. Do you wanna use it?"):
                                        os.remove(_path)
                                        create_file()

                    else:
                        create_file()


            await tree.for_each(for_each)

    asyncio.new_event_loop().run_until_complete(main())


@command.command()
@click.option('--force', '-f', is_flag=True, default=False, help='Replacing the files with the new (force)')
def push(force: bool):
    Request.COOKIES = cookiejar_from_dict(Config().get("cookies", {}))

    from scriptor.module import TreeModule
    tree = TreeModule("script")

    async def main():
        try:
            await tree.structure("node")
        except:
            click.echo("Failed to push... Is the script module included?")
            return

        working_dir = Config().get("WORKING_DIR", DEFAULT_WORKING_DIR)
        if working_dir:
            _files = glob.glob(f"{working_dir}/**/*", recursive=True)
            for file in _files:
                _real_file = file
                parent = os.path.dirname(file)
                _type = "leaf"
                if os.path.isdir(file):
                    _type = "node"

                tmp = working_dir
                if not working_dir.endswith("/"):
                    tmp += "/"
                file = file.removeprefix(tmp)
                if _type == "node":
                    file += "/"


                is_root = False
                parent = parent.removeprefix(tmp).removeprefix(working_dir.replace("/", ""))
                if not parent:
                    is_root = True

                try:
                    entry = await anext(tree.list(_type, {"path": file}))
                    if _type == "leaf":
                        online_content = entry["script"].replace("\r", "").encode("utf-8")
                        with open(_real_file, "r") as f:
                            file_content = f.read().replace("\r", "").encode("utf-8")
                            if hashlib.sha256(online_content).digest() != hashlib.sha256(file_content).digest():
                                _state = click.confirm(f"The content of the {file} is not up to date, Should we overwrite it?") if not force else True
                                if _state:
                                    await tree.edit(_type, entry["key"], {
                                        "script": file_content
                                    })
                except StopAsyncIteration:
                    _state = False
                    text = "directory"
                    if _type == "leaf":
                        text = "file"

                    _state = click.confirm(f"There is no {text}: '{file}'. Should I create it?") if not force else True
                    if _state:
                        root_node_entry = (await tree.list_root_nodes())[0]

                        if not parent.endswith("/"):
                            parent += "/"

                        parent_entry = root_node_entry
                        if not is_root:
                            parent_entry = await anext(tree.list("node", {"path": parent}))

                        last = file
                        if file.count("/") > 0:
                            _split = [_f for _f in file.split("/") if _f]
                            last = _split[len(_split) - 1]

                        args = {
                            "name": last,
                            "parentrepo": root_node_entry["key"],
                            "parententry": parent_entry["key"],
                            "rootNode": False,
                            "path": file,
                            "plugin": False
                        }

                        if _type != "node":
                            update_file = False
                            with open(_real_file, "r") as f:
                                args.update({
                                    "script": f.read()
                                })

                                if not args["script"]:
                                    args["script"] = "#### scriptor ####"
                                    update_file = True
                            if update_file:
                                with open(_real_file, "w") as f:
                                    f.truncate()
                                    f.write(args["script"])

                        await tree.add(_type, args)

    asyncio.new_event_loop().run_until_complete(main())


@command.command()
@click.option('--path', help='Path of the file in the working directory')
def run(path: str):
    Request.COOKIES = cookiejar_from_dict(Config().get("cookies", {}))

    if not path:
        click.echo("You need to enter a file path to execute.")
        return

    working_dir = Config().get("WORKING_DIR", DEFAULT_WORKING_DIR)
    sys.path.append(working_dir)
    _file_path = os.path.join(working_dir, path)
    _file_path = _file_path.replace("/", ".")

    async def main():
        await init()
        import logging
        logging.getLogger().setLevel(logging.INFO)
        import importlib
        p = path.replace(".py", "")
        p = p.replace("/", ".")
        module = importlib.import_module(p)
        await module.main()

    asyncio.new_event_loop().run_until_complete(main())



