from .utils import is_pyodide_context

if is_pyodide_context():
    from js import self as _self
else:
    import logging

import json


class Logging():
    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    @staticmethod
    def format_text(*args, **kwargs):
        jsonify = False
        if any([isinstance(arg, (dict, list)) for arg in args]):
            jsonify = True

        text = ""
        if jsonify:
            try:
                if is_pyodide_context():
                    text = json.dumps(args)
                else:
                    text = json.dumps(args, sort_keys=True, indent=4)
            except:
                text = ""

        if not text:
            delimiter = kwargs.get("sep", " ")
            text = f"{delimiter}".join([str(arg) for arg in args])

        return text

    @staticmethod
    def set_level(level: int):
        if not is_pyodide_context():
            logging.getLogger().setLevel(level)

    @staticmethod
    def debug(*args, **kwargs):
        text = Logging.format_text(*args, **kwargs)
        if is_pyodide_context():
            _self.postMessage(type="log", text=text, level="debug")
        else:
            logging.debug(text)

    @staticmethod
    def info(*args, **kwargs):
        text = Logging.format_text(*args, **kwargs)
        if is_pyodide_context():
            _self.postMessage(type="log", text=text, level="info")
        else:
            logging.info(text)

    @staticmethod
    def warning(*args, **kwargs):
        text = Logging.format_text(*args, **kwargs)

        if is_pyodide_context():
            _self.postMessage(type="log", text=text, level="warning")
        else:
            logging.warning(text)

    @staticmethod
    def error(*args, **kwargs):
        text = Logging.format_text(*args, **kwargs)

        if is_pyodide_context():
            _self.postMessage(type="log", text=Logging.format_text(*args, **kwargs), level="error")
        else:
            logging.error(text)
