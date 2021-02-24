from typing import List, Dict, Callable, Any, NamedTuple, TYPE_CHECKING
from pyri.plugins import util as plugin_util

if TYPE_CHECKING:
    from .. import PyriWebUIBrowser

class PyriWebUIBrowserPanelInfo(NamedTuple):
    title: str
    panel_type: str
    priority: int

class PyriWebUIBrowserPanelBase:
    pass

class PyriWebUIBrowserPanelPluginFactory:
    def __init__(self):
        super().__init__()

    def get_plugin_name(self) -> str:
        return ""

    def get_panels_infos(self) -> Dict[str,PyriWebUIBrowserPanelInfo]:
        return []

    async def add_panel(self, panel_type: str, core: "PyriWebUIBrowser", parent_element: Any) -> PyriWebUIBrowserPanelBase:
        raise NotImplementedError()

def get_webui_browser_panel_factories() -> List[PyriWebUIBrowserPanelPluginFactory]:
    return plugin_util.get_plugin_factories("pyri.plugins.webui_browser_panel")

def get_all_webui_browser_panels_infos() -> Dict[str,Any]:
    ret = dict()
    factories = get_webui_browser_panel_factories()
    for factory in factories:
        ret[factory.get_plugin_name()] = factory.get_panels_infos()
    return ret

async def add_webui_browser_panel(panel_type: str, core: "PyriWebUIBrowser", parent_element: Any) -> Dict[str,Any]:
    
    factories = get_webui_browser_panel_factories()
    for factory in factories:
        infos = factory.get_panels_infos()
        if panel_type in infos:
            return await factory.add_panel(panel_type, core, parent_element)

    assert False, f"Unknown panel_type \"{panel_type}\" specified"
    