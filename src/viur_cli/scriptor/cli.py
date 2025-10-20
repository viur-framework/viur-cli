import datetime
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
from viur.scriptor import Modules
from ..cli import cli
from ..cli import scriptor_config

# Global modules instance that will be initialized when needed
_modules = None


def get_modules():
    """Get or create the global Modules instance"""
    global _modules
    if _modules is None:
        _modules = Modules(scriptor_config["base_url"], cookies=scriptor_config["cookies"])
        asyncio.new_event_loop().run_until_complete(_modules.init())

    return _modules


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


    if url:
        scriptor_config["base_url"] = url

    if username:
        scriptor_config["username"] = username

    if working_dir:
        scriptor_config["working_dir"] = working_dir.replace("\\", "/")


@script.command()
def setup():
    """
    Setup user session with a given username and password.
    """

    base_url = scriptor_config.get("base_url")
    try:
        session = requests.session()
        skey = session.get(base_url + "/json/skey")
        username: str = scriptor_config.get("username", "")
        if not username:
            username = click.prompt("Enter the username")

        password: str = click.prompt("Enter the password", hide_input=True)

        response = session.post(base_url + "/json/user/auth_userpassword/login", data={
            "skey": skey.json(),
            "name": username,
            "password": password
        })

        if response.json() != "FAILURE":
            scriptor_config["cookies"] = session.cookies.get_dict()
            scriptor_config.save()
            click.echo("Setup done")
        else:
            if "cookies" in scriptor_config:
                del scriptor_config["cookies"]
            click.echo("Failed to login. Did you maybe entered the wrong password?")
    except KeyboardInterrupt:
        pass


def check_session(ctx: click.Context):
    base_url = scriptor_config.get("base_url")

    s = requests.Session()
    s.cookies = cookiejar_from_dict(scriptor_config.get("cookies", {}))

    response = s.get(base_url + "/vi/user/view/self", cookies=scriptor_config.get("cookies", {}))
    if not response.ok:
        click.echo("Invalid session, please run `viur script setup` again.")
        ctx.invoke(setup)
        ctx.close()
    #FIXME We need this ?
    # Update modules with cookies
    modules = get_modules()
    # modules.request.cookies = cookiejar_from_dict(scriptor_config.get("cookies", {}))


@script.command()
@click.option('--force', default=False, help='Force replace files from server in local working directory')
@click.pass_context
def pull(ctx: click.Context, force: bool):
    """
    Pull contents from server to working_dir.
    """
    check_session(ctx)


    async def main():
        # In the new API, we don't need to call structure
        modules = get_modules()
        tree = await modules.get_module("script")
        working_dir = scriptor_config.get("working_dir")

        async def process_entry(entry: dict, is_node: bool):
            _path = os.path.join(working_dir, entry["path"])

            if is_node:
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

        # Process nodes first
        async for node in tree.list(skel_type="node"):
            await process_entry(node, True)

        # Then process leaves
        async for leaf in tree.list(skel_type="leaf"):
            await process_entry(leaf, False)

    asyncio.new_event_loop().run_until_complete(main())


@script.command()
@click.option('--force', '-f', is_flag=True, default=False,
              help='Force push files from the local working directory onto the server')
@click.option('--watch', '-w', is_flag=True, default=False,
              help="Watch for file changes in the script folder and push them to the server")
@click.pass_context
def push(ctx: click.Context, force: bool, watch: bool):
    """
    Push contents of working_dir to server.
    """

    check_session(ctx)

    async def main(file_path: str = None):
        modules = get_modules()
        tree = await modules.get_module("script")

        # In the new API, we don't need to call structure
        working_dir = scriptor_config.get("working_dir")
        _files = glob.glob(f"{working_dir}/**/*", recursive=True)
        for file in _files:
            _real_file = file
            if file_path and file_path != _real_file:
                # only push a single file
                continue
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
                # Search for the entry with the given path
                entry = None
                async for item in tree.list(skel_type=_type):
                    if item.get("path") == file:
                        entry = item
                        break

                if not entry:
                    raise StopAsyncIteration
                if _type == "leaf":
                    with open(_real_file, "r") as f:
                        file_content = f.read()

                        if hashlib.sha256(entry["script"].encode("utf-8")).digest() \
                                != hashlib.sha256(file_content.encode("utf-8")).digest():
                            can_push = force
                            if not can_push:
                                can_push = click.confirm(f"Content of {file} changed. Overwrite?")

                            if can_push:
                                date = datetime.datetime.now().strftime("%H:%M:%S")
                                click.echo(f"{date if watch else ""} Push {_real_file}")
                                await tree.edit(entry["key"], {
                                    "script": file_content
                                }, skel_type=_type)

            except StopAsyncIteration:
                text = "folder"
                if _type == "leaf":
                    text = "file"

                can_push = force
                if not can_push:
                    can_push = click.confirm(f"There is no {text} named {file}. Create it?")

                if can_push:
                    # Get the root node
                    root_node_entry = None
                    async for node in tree.list(skel_type="node"):
                        if node.get("parententry") is None:
                            root_node_entry = node
                            break

                    if not parent.endswith("/"):
                        parent += "/"

                    parent_entry = root_node_entry
                    if not is_root:
                        # Find parent entry
                        parent_entry = None
                        async for node in tree.list(skel_type="node"):
                            if node.get("path") == parent:
                                parent_entry = node
                                break

                    last = file
                    if file.count("/") > 0:
                        _split = [_f for _f in file.split("/") if _f]
                        last = _split[len(_split) - 1]

                    args = {
                        "name": last,
                        # "parentrepo": root_node_entry["key"],
                        # "parententry": parent_entry["key"],
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

    if watch:
        print("Watching...")

        def watch_loop():
            from watchdog.events import RegexMatchingEventHandler
            from watchdog.observers import Observer
            import time
            modified_files = {}

            def on_modified(event):
                try:
                    # check for tmp file
                    if event.src_path.endswith("~"):
                        return
                    if event.src_path not in modified_files:
                        modified_files[event.src_path] = os.path.getmtime(event.src_path)
                    elif os.path.getmtime(event.src_path) == modified_files[event.src_path]:
                        return
                    modified_files[event.src_path] = os.path.getmtime(event.src_path)
                    asyncio.new_event_loop().run_until_complete(main(event.src_path))
                except Exception as e:
                    import traceback
                    print(f"Error: on file {event.src_path} {e}")
                    traceback.print_exc()

            regexes = [r".*\.py"]
            ignore_regexes = []
            ignore_directories = True
            case_sensitive = False
            event_handler = RegexMatchingEventHandler(
                regexes=regexes,
                ignore_regexes=ignore_regexes,
                ignore_directories=ignore_directories,
                case_sensitive=case_sensitive
            )
            event_handler.on_modified = on_modified

            observer = Observer()
            observer.schedule(event_handler, scriptor_config.get("working_dir"), recursive=True)
            observer.start()
            try:
                while True:
                    time.sleep(1)
            finally:
                observer.stop()
                observer.join()

        asyncio.new_event_loop().run_until_complete(watch_loop())
        return
    asyncio.new_event_loop().run_until_complete(main())


@script.command()
@click.argument('path', required=True)
@click.argument("args", nargs=-1)
@click.pass_context
def run(ctx: click.Context, path: str, args=None):
    """
    Locally run a script located in the working_dir.
    """
    check_session(ctx)

    for dir in (os.path.dirname(os.path.realpath(__file__)), scriptor_config.get("working_dir")):
        if dir not in sys.path:
            sys.path.insert(0, dir)

    async def main():
        # The new API doesn't need explicit init
        import logging
        import importlib
        logging.getLogger().setLevel(logging.INFO)
        import viur.scriptor
        await viur.scriptor._init_modules(
            script_params=args,
            base_url=scriptor_config["base_url"],
            cookies=scriptor_config["cookies"]
        )
        # fixme: there should be a better method than this below
        module = importlib.import_module(path.replace("/", ".").removesuffix(".py"))

        await module.main()

    asyncio.new_event_loop().run_until_complete(main())
