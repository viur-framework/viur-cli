from .network import Request
from .utils import is_pyodide_context
from urllib.parse import urlencode as _urlencode

if is_pyodide_context():
    from js import console, fetch
    from config import BASE_URL


class viur:
    class request(Request):
        def __init__(self, method: str, url: str, params=None, renderer: str = None):

            if not url.startswith("/"):
                url = "/" + url

            prefix = "/json"
            if renderer:
                prefix = "/" + renderer

            url = self.build_url(prefix + url)

            super().__init__(
                method,
                url,
                credentials=True,
                data=params,
                headers={
                    "Accept": "application/json, text/plain, */*",
                }
            )

        @staticmethod
        def build_url(url):
            if url and not (url.startswith('http://') or url.startswith('https://') or url.startswith('//')):
                url = BASE_URL + url

            return url

        @staticmethod
        async def get(*args, **kwargs):
            _request = viur.request("GET", *args, **kwargs)
            await _request.perform()
            return await _request.json()

        @staticmethod
        async def post(*args, **kwargs):
            _request = viur.request("POST", *args, **kwargs)
            await _request.perform()

            return await _request.json()

        @staticmethod
        async def secure_post(url, params=None, renderer: str = None):
            req = viur.request("GET", "/skey", renderer=renderer)
            await req.perform()

            skey = await req.json()
            if not params:
                params = {
                    "skey": skey
                }
            else:
                params.update({
                    "skey": skey
                })

            return await viur.request.post(url, params, renderer)

    @staticmethod
    def build_url(action: str, url: str, module: str, group: str = "", key: str = ""):
        _url = url
        if not _url:
            assert module, "You need to set an url or use the module parameter."
            _url = f"{module}/{action}"
            if group:
                _url += f"/{group}"
            if key:
                _url += f"/{key}"
        return _url

    @staticmethod
    async def view(*, url: str = "", module: str = "", key: str = "", params: dict = None, group: str = "", **kwargs):
        _url = viur.build_url("view", url, module, group, key)

        if not (ret := await viur.request.get(_url, params, **kwargs)):
            return ret

        return ret["values"]

    @staticmethod
    async def edit(*, url: str = "", module: str = "", key: str = "", params: dict = None, group: str = "", **kwargs):
        url = viur.build_url("edit", url, module, group, key)

        if not (ret := await viur.request.secure_post(url, params, **kwargs)):
            return ret

        return ret

    @staticmethod
    async def structure(*, url: str = "", module: str = "", group: str = "", **kwargs):
        url = viur.build_url("structure", url, module, group)

        if not (ret := await viur.request.get(url, **kwargs)):
            return ret

        return ret

    @staticmethod
    async def preview(*, url: str = "", module: str = "", group: str = "", params: dict = None, **kwargs):
        url = viur.build_url("preview", url, module, group)

        if not (ret := await viur.request.secure_post(url, params, **kwargs)):
            return ret

        return ret

    @staticmethod
    async def add(*, url: str = "", module: str = "", params: dict = None, group: str = "", **kwargs):
        url = viur.build_url("add", url, module, group)

        if not (ret := await viur.request.secure_post(url, params, **kwargs)):
            return ret

        return ret

    @staticmethod
    async def delete(*, url: str = "", module: str = "", key: str = "", params: dict = None, group: str = "", **kwargs):
        url = viur.build_url("delete", url, module, group, key)

        if not (ret := await viur.request.secure_post(url, params, **kwargs)):
            return ret

        return ret

    @staticmethod
    async def list_root_nodes(*, url: str = "", module: str = "", params: dict = None, group: str = "", **kwargs):
        _url = viur.build_url("view", url, module, group)

        if not (ret := await viur.request.get(_url, params, **kwargs)):
            return ret

        return ret["values"]

    class list:
        """
        Fetches a list from a VIUR module
        """

        def __init__(self, *, url: str = "", module: str = "", params: dict = None, group: str = "",
                     renderer: str = ""):
            self._module = module
            self._params = params or {}
            if not url:
                assert module, "You need to set an url or use the module parameter."
                self._url = f"{module}/{self.__class__.__name__}"
                if group:
                    self._url += f"/{group}"
            else:
                self._url = url

            self._renderer = renderer

            self.batch = []
            self.cursor = None
            self.fetched = False

        def __aiter__(self):
            self.cursor = None
            self.fetched = False
            return self

        async def __anext__(self):
            if self.batch:
                return self.batch.pop()

            if self.fetched and not self.cursor:
                raise StopAsyncIteration

            if self.cursor:
                self._params["cursor"] = self.cursor

            ret = await viur.request.get(self._url, self._params, renderer=self._renderer)
            self.fetched = True

            if not ret:
                raise StopAsyncIteration

            self.batch = ret["skellist"]
            self.cursor = ret["cursor"]

            if not self.batch:
                self.cursor = None

            return await self.__anext__()
