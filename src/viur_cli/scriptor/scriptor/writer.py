from io import StringIO
from .utils import is_pyodide_context

if is_pyodide_context():
    from js import eval as js_eval, self as _self, Blob
    from pyodide.ffi import to_js, create_once_callable
# import js_utils

from .logger import Logging as logging


class WriterBase:
    LINE_TERMINATOR = '\n'

    def __init__(self, line_terminator=LINE_TERMINATOR) -> None:
        self._line_count = 0
        self._offset = 0
        self._line_terminator = line_terminator

    def increase_line_count(self):
        self._line_count += 1

    @property
    def line_terminator(self) -> str:
        return self._line_terminator

    @line_terminator.setter
    def line_terminator(self, value: str):
        self._line_terminator = value

    @property
    def line_count(self) -> int:
        return self._line_count

    @property
    def offset(self):
        return self._offset

    def __len__(self) -> int:
        return self._line_count

    def write(self, content: str):
        pass

    def write_line(self, content: str):
        pass

    def write_lines(self, lines: list[str]):
        for line in lines:
            self.write_line(line)


class MemoryWriter(WriterBase):
    DEFAULT_FILE_NAME = "export.txt"

    def __init__(self, content: str = "") -> None:
        self._content = StringIO(content)
        super().__init__()

    def write(self, content: str):
        self._content.write(content)
        self._line_count = self._content.getvalue().count(self._line_terminator)
        self._offset = 0

    def write_line(self, content: str):
        self.increase_line_count()
        _line = content + self._line_terminator
        self._content.write(_line)
        self._offset += len(_line)

    def __str__(self) -> str:
        return self._content.getvalue()

    def clear(self):
        self._content.truncate()

    def download(self, name: str = ""):

        if not name:
            name = self.DEFAULT_FILE_NAME

        if is_pyodide_context():
            blob = Blob.new([str(self)], **{
                "type": "application/csv;charset=utf-8;"
            })

            _self.postMessage(type="download", blob=blob, filename=name)
        else:
            with open(name, "w") as f:
                f.write(str(self))


if 1:
    from .dialog import wait

    if is_pyodide_context():
        import manager
    else:
        import os
        import click


    class Picker:
        TYPE_NAME = ""

        async def on_startup(self):
            pass

        @classmethod
        async def open(cls):
            # js_utils.registerEvent(cls.EVENT_NAME, create_once_callable(lambda handle, cb=callback: cls.on_handle_callback(handle, cb)))
            if is_pyodide_context():
                _self.postMessage(type=cls.TYPE_NAME)
                await wait()

                tmp = manager.copyResult()
                manager.reset()
                manager.resultValue = None

                if tmp == -1 or not tmp:
                    return None

                instance = cls(tmp)
            else:
                ret = click.prompt("Enter a path")

                if cls.TYPE_NAME == "showOpenFilePicker":
                    instance = cls([open(ret, "r")])
                else:
                    instance = cls(ret)

            await instance.on_startup()
            return instance


    class FilePickerWriter(WriterBase, Picker):
        TYPE_NAME = "showSaveFilePicker"

        def __init__(self, file_object: object, line_terminator: str = WriterBase.LINE_TERMINATOR) -> str:
            super().__init__(line_terminator)
            self._file = file_object
            self._file_stream = None

        async def write(self, content: str):
            if is_pyodide_context():
                await self._file_stream.write(
                    type="write",
                    data=content
                )
            else:
                self._file_stream.seek(self._offset)
                self._file_stream.write(content)

            self._offset += len(content)
            self.increase_line_count()

        async def write_line(self, content: str):
            content = content + self.line_terminator
            # FIX WRITING!!

            if is_pyodide_context():
                encoder = js_eval("new TextEncoder()")

                await self._file_stream.write(
                    type="write",
                    data=encoder.encode(content)
                )
            else:
                self._file_stream.seek(self._offset)
                self._file_stream.write(content)

            self._offset += len(content)
            self.increase_line_count()

        async def close(self):
            if is_pyodide_context():
                await self._file_stream.close()
            else:
                self._file_stream.close()

        async def __aenter__(self):
            if is_pyodide_context():
                self._file_stream = await self._file.createWritable()
            else:
                self._file_stream = open(self._file, "a+")
                self._file_stream.truncate()

        async def __aexit__(self, *args):
            await self.close()

        def __len__(self):
            return len(str(self._file))


    class DirectoryPickerWriter(WriterBase, Picker):
        TYPE_NAME = "showDirectoryPicker"

        def __init__(self, directory_handle: object, line_terminator: str = WriterBase.LINE_TERMINATOR,
                     parent_handle: object = None) -> str:
            super().__init__(line_terminator)
            self._directory_handle = directory_handle
            if not is_pyodide_context():
                if not os.path.exists(self._directory_handle):
                    os.makedirs(self._directory_handle)

            self._parent_handle = parent_handle

        async def file(self, path: str):
            if self._directory_handle is None:
                return None

            if is_pyodide_context():
                return FilePickerWriter(await self._directory_handle.getFileHandle(path, create=True),
                                        WriterBase.LINE_TERMINATOR)

            return FilePickerWriter(os.path.join(self._directory_handle, path), WriterBase.LINE_TERMINATOR)

        async def directory(self, path: str):
            if self._directory_handle is None:
                return None

            if is_pyodide_context():
                return DirectoryPickerWriter(await self._directory_handle.getDirectoryHandle(path, create=True),
                                             WriterBase.LINE_TERMINATOR, self._directory_handle)

            return DirectoryPickerWriter(os.path.join(self._directory_handle, path), WriterBase.LINE_TERMINATOR,
                                         self._directory_handle)

        def __len__(self):
            return len(str(self._directory_handle))
