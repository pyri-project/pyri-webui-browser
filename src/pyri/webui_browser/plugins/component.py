from typing import List, Dict, Callable, Any, NamedTuple, TYPE_CHECKING, Tuple
from pyri.plugins import util as plugin_util

class PyriWebUIBrowserComponentPluginFactory:
    def __init__(self):
        pass

    def get_plugin_name(self) -> str:
        return ""

    def register_components(self) -> None:
        pass

def get_webui_browser_component_factories() -> List[PyriWebUIBrowserComponentPluginFactory]:
    return plugin_util.get_plugin_factories("pyri.plugins.webui_browser_component")

def register_all_webui_browser_components() -> None:
    factories = get_webui_browser_component_factories()
    for factory in factories:
        factory.register_components()