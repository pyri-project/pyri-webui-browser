from typing import List, Dict, Callable, Any, NamedTuple, TYPE_CHECKING, Tuple, Awaitable
from .plugins.plugin_init import PyriWebUIPluginInitFactory

import js

if TYPE_CHECKING:
    from . import PyriWebUIBrowser

async def plugin_init(core: "PyriWebUIBrowser"):

    await core.js_loader.load_js_src("/deps/golden-layout/dist/bundle/umd/golden-layout.js", script_type="module")
    await core.js_loader.load_js_src("/deps/golden-layout/dist/css/goldenlayout-base.css")
    await core.js_loader.load_js_src("/deps/golden-layout/dist/css/themes/goldenlayout-light-theme.css")
    await core.js_loader.load_js_src("./style.css")
    await core.js_loader.load_js_src("/deps/bootstrap/dist/css/bootstrap.min.css")
    await core.js_loader.load_js_src("/deps/bootstrap-vue/dist/bootstrap-vue.min.css")
    await core.js_loader.load_js_src("/deps/bootstrap-table/dist/bootstrap-table.min.css")
    await core.js_loader.load_js_src("/deps/@fortawesome/fontawesome-free/css/all.min.css")
    await core.js_loader.load_js_src("/deps/vue/dist/vue.js")
    await core.js_loader.load_js_src("/deps/bootstrap-vue/dist/bootstrap-vue.js")
    await core.js_loader.load_js_src("/deps/bootstrap-table/dist/bootstrap-table.js")
    await core.js_loader.load_js_src("/deps/bootstrap-table/dist/bootstrap-table-vue.js")
    await core.js_loader.load_js_src("/deps/cropperjs/dist/cropper.min.js")
    await core.js_loader.load_js_src("/deps/cropperjs/dist/cropper.min.css")


    js.window.Vue.use(js.window.BootstrapVue)

class PyriBrowserWebUIPluginInitFactory(PyriWebUIPluginInitFactory):

    def get_plugin_name(self) -> str:
        return "pyri-webui-browser"

    def get_plugin_init(self) -> Tuple[Callable[["PyriWebUIBrowser"], Awaitable], List[str]]:
        return plugin_init, []

def get_webui_browser_plugin_init_factory():
    return PyriBrowserWebUIPluginInitFactory()