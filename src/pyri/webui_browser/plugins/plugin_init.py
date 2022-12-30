from typing import List, Dict, Callable, Any, NamedTuple, TYPE_CHECKING, Tuple, Awaitable
from pyri.plugins import util as plugin_util
import warnings

if TYPE_CHECKING:
    from .. import PyriWebUIBrowser

class PyriWebUIPluginInitFactory:

    def __init__(self):
        pass

    def get_plugin_name(self) -> str:
        return ""

    async def get_plugin_init(self) -> Tuple[Callable[["PyriWebUIBrowser"],Awaitable],List[str]]:
        pass

def get_webui_browser_plugin_init_factories() -> List[PyriWebUIPluginInitFactory]:
    return plugin_util.get_plugin_factories("pyri.plugins.webui_browser_plugin_init")

async def plugin_init_all_webui_plugins(core: "PyriWebUIBrowser") -> None:
    factories = get_webui_browser_plugin_init_factories()  
    init_funcs = dict()
    init_requires = dict()
    for factory in factories:
        plugin_name = factory.get_plugin_name()
        init_func, init_require = factory.get_plugin_init()
        init_funcs[plugin_name] = init_func
        init_requires[plugin_name] = set(init_require)

    for plugin_name, init_require in init_requires.items():
        for r in init_require:
            if r not in init_requires.keys():
                warnings.warn("PyriWebUIPlugin {plugin_name} expects unavailable plugin {r}")

    uninitialized_plugins = set(init_requires.keys())

    while len(uninitialized_plugins) > 0:
        for plugin_name in uninitialized_plugins:
            if uninitialized_plugins.isdisjoint(init_requires[plugin_name]):
                uninitialized_plugins.remove(plugin_name)
                await init_funcs[plugin_name](core)
                break

        
