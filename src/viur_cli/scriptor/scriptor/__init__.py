import asyncio

from .utils import get_json_object, is_pyodide_context

from .network import Request
from .viur import viur
from .csvwriter import MemoryCsvWriter, FileSystemCsvWriter
from .logger import Logging as logging
from .module import ListModule, SingletonModule, TreeModule

from .writer import DirectoryPickerWriter, FilePickerWriter, MemoryWriter
from .readers import FilePickerReader

try:
    from js import console
except ModuleNotFoundError:
    pass

import json
import copy

old_print = print


def print(*args, **kwargs):
    if is_pyodide_context():
        logging.info(*args, **kwargs)
    else:
        old_print(logging.format_text(*args, **kwargs))


from .utils import sleep


class prototypes:
    list = ListModule
    singleton = SingletonModule
    tree = TreeModule


viur.prototypes = prototypes()

try:
    viur.modules
except AttributeError:
    viur.modules = []


async def init():
    resp = await viur.request.get("/config", renderer="vi")
    viur.modules = resp["modules"]
    if is_pyodide_context():
        console.log("response = ", resp)
