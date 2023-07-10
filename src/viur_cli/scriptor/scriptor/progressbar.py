from .utils import is_pyodide_context

if is_pyodide_context():
    from js import self as _self


def start(total: int, step: int = -1, max_step: int = -1, txt=""):
    if is_pyodide_context():
        _self.postMessage(type="progressbar", total=total, step=step, max_step=max_step, txt=txt)


def stop():
    start(100)


def update(*args, **kwargs):
    start(*args, **kwargs)
