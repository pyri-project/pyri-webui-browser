import asyncio
import js

class JsLoader:
    def __init__(self):
        self.loading_url = set()
        self.loaded_url = set()

    async def load_js_src(self, script_url):

        if script_url in self.loading_url:
            return

        fut = asyncio.Future()

        def onload(evt):
            print(f"jsloader onload {evt}")
            fut.set_result(True)

        def onerror(evt):
            print(f"jsloader onerror {evt.message}")
            fut.set_exception(Exception(evt.message))

        if script_url.endswith(".css"):
            script = js.document.createElement('link')
            script.rel = "stylesheet"
            script.href = script_url
            script.type = "text/css"
        else:
            script = js.document.createElement('script')
            script.src = script_url
        script.onload = onload
        script.onerror = onerror

        js.document.head.appendChild(script)

        self.loading_url.add(script_url)
        print("Begin wait url")
        await fut
        print("End wait url")
        self.loaded_url.add(script_url)

    