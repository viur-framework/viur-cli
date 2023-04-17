import click
import json
import requests
import os
import hashlib
import asyncio
import sys
import glob
from requests.sessions import cookiejar_from_dict
from weakref import proxy
from .scriptor import Request, init, viur
from ..cli import cli


class Config(dict):
    """
    Manage scriptor configuration.
    """
    CONFIG_FILE_NAME = "viur_scriptor_config.json"
    DEFAULT_BASE_URL = "http://localhost:8080"
    DEFAULT_WORKING_DIR = "scripts/"

    def __new__(cls):
        if not getattr(cls, "_instance", None):
            cls._instance = super().__new__(cls)

            # use defaults in config
            cls._instance |= {
                "base_url": cls.DEFAULT_BASE_URL,
                "working_dir": cls.DEFAULT_WORKING_DIR,
            }

            if os.path.exists(cls.CONFIG_FILE_NAME):
                with open(cls.CONFIG_FILE_NAME, "r") as f:
                    cls._instance |= json.load(f)

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


def build_url(url: str):
    return Config()["base_url"] + "/" + url

viur.request.build_url = staticmethod(build_url)


@cli.group()
def script():
    """
    Manage and run scriptor scripts locally on the console
    """


@script.command()
@click.option('--url', default=None, help='Set the url')
@click.option('--username', default=None, help='Set the username')
@click.option('--working_dir', default=None, help='Set the working directory where scripts are stored to')
def configure(url: str, username: str, working_dir: str):
    """
    Manage configuration settings.
    """
    conf = Config()

    if url:
        conf["base_url"] = url

    if username:
        conf["username"] = username

    if working_dir:
        conf["working_dir"] = working_dir.replace("\\", "/")


@script.command()
def setup():
    """
    Setup user session with a given username and password.
    """
    config = Config()
    base_url = config.get("base_url")
    try:
        session = requests.session()
        skey = session.get(base_url + "/json/skey")
        username: str = config.get("username", "")
        if not username:
            username = click.prompt("Enter the username")

        password: str = click.prompt("Enter the password", hide_input=True)

        response = session.post(base_url + "/json/user/auth_userpassword/login", data={
            "skey": skey.json(),
            "name": username,
            "password": password
        })

        if response.json() != "FAILURE":
            config["cookies"] = session.cookies.get_dict()
            click.echo("Setup done")
        else:
            if "cookies" in config:
                del config["cookies"]
            click.echo("Failed to login. Did you maybe entered the wrong password?")
    except KeyboardInterrupt:
        pass


def check_session(ctx: click.Context):
    base_url = Config().get("base_url")

    s = requests.Session()
    s.cookies = cookiejar_from_dict(Config().get("cookies", {}))

    response = s.get(base_url+"/vi/user/view/self", cookies=Config().get("cookies", {}))
    if not response.ok:
        click.echo("Invalid session, please run `viur script setup` again.")
        ctx.invoke(setup)
        ctx.close()

@script.command()
@click.option('--force', default=False, help='Force replace files from server in local working directory')
@click.pass_context
def pull(ctx: click.Context, force: bool):
    """
    Pull contents from server to working_dir.
    """
    check_session(ctx)
    Request.COOKIES = cookiejar_from_dict(Config().get("cookies", {}))
    from .scriptor.module import TreeModule
    tree = TreeModule("script")

    async def main():
        await tree.structure("node")

        working_dir = Config().get("working_dir")
        async def for_each(group: str, entry: object):
            _path = os.path.join(working_dir, entry["path"])

            if group == "node":
                if not os.path.exists(_path):
                    os.makedirs(_path)

            else:
                def create_file():
                    with open(_path, "a+") as f:
                        f.write(entry["script"])

                    click.echo(f"Pull {_path}")

                if os.path.exists(_path):
                    if force:
                        os.remove(_path)
                        create_file()
                    else:
                        with open(_path, "r") as f:
                            if hashlib.sha256(entry["script"].encode()).digest() \
                                    != hashlib.sha256(f.read().encode()).digest():
                                if click.confirm(f"There is a difference with {entry['path']}. Overwrite?"):
                                    os.remove(_path)
                                    create_file()

                else:
                    create_file()

        await tree.for_each(for_each)

    asyncio.new_event_loop().run_until_complete(main())


@script.command()
@click.option('--force', '-f', is_flag=True, default=False,
              help='Force push files from the local working directory onto the server')
@click.pass_context
def push(ctx: click.Context, force: bool):
    """
    Push contents of working_dir to server.
    """
    check_session(ctx)
    Request.COOKIES = cookiejar_from_dict(Config().get("cookies", {}))

    from .scriptor.module import TreeModule
    tree = TreeModule("script")

    async def main():
        await tree.structure("node")

        working_dir = Config().get("working_dir")
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
                    with open(_real_file, "r") as f:
                        file_content = f.read()

                        if hashlib.sha256(entry["script"].encode("utf-8")).digest() \
                                != hashlib.sha256(file_content.encode("utf-8")).digest():
                            _state = force
                            if not _state:
                                _state = click.confirm(f"Content of {file} changed. Overwrite?")

                            if _state:
                                click.echo(f"Push {_real_file}")
                                await tree.edit(_type, entry["key"], {
                                    "script": file_content
                                })

            except StopAsyncIteration:
                _state = False
                text = "folder"
                if _type == "leaf":
                    text = "file"

                _state = force
                if not _state:
                    _state = click.confirm(f"There is no {text} named {file}. Create it?")

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
                        #"parentrepo": root_node_entry["key"],
                        #"parententry": parent_entry["key"],
                        "node": parent_entry["key"],
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

                    click.echo(f"Push {_real_file}")
                    await tree.add(_type, args)

    asyncio.new_event_loop().run_until_complete(main())


@script.command()
@click.argument('path', required=True)
@click.pass_context
def run(ctx: click.Context, path: str):
    """
    Locally run a script located in the working_dir.
    """
    check_session(ctx)
    Request.COOKIES = cookiejar_from_dict(Config().get("cookies", {}))

    for dir in (os.path.dirname(os.path.realpath(__file__)), Config().get("working_dir")):
        if dir not in sys.path:
            sys.path.insert(0, dir)

    async def main():
        await init()
        import logging
        import importlib
        logging.getLogger().setLevel(logging.INFO)

        # fixme: there should be a better method than this below
        module = importlib.import_module(path.replace("/", ".").removesuffix(".py"))

        await module.main()

    asyncio.new_event_loop().run_until_complete(main())
