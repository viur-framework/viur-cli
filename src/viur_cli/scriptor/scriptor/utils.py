import sys
import json


def is_pyodide_context():
    return sys.platform == 'emscripten' or "pyodide" in sys.modules


def get_json_object(text: str):
    try:
        return json.loads(text)
    except ValueError as e:
        return False
    return True


async def sleep(ms: int):
    if is_pyodide_context():
        import manager
        await manager.sleep(ms)
    else:
        import asyncio
        if ms > 0 or ms < 0:
            ms = float(ms) / 1000.0
        await asyncio.sleep(ms)
