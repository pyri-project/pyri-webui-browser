from typing import List, Dict, Callable, Any, NamedTuple, TYPE_CHECKING, Tuple
from pyri.plugins import util as plugin_util

if TYPE_CHECKING:
    from ..golden_layout import PyriGoldenLayoutPanelConfig

class PyriWebUIBrowserPanelInfo(NamedTuple):
    title: str
    description: str
    panel_type: str
    panel_category: str
    component_type: str
    priority: int

class PyriWebUIBrowserPanelPluginFactory:
    def __init__(self):
        super().__init__()

    def get_plugin_name(self) -> str:
        return ""

    def get_panels_infos(self) -> Dict[str,PyriWebUIBrowserPanelInfo]:
        return []

    def get_default_panels(self, layout_config: str = "default") -> List[Tuple[PyriWebUIBrowserPanelInfo,"PyriGoldenLayoutPanelConfig"]]:
        pass

def get_webui_browser_panel_factories() -> List[PyriWebUIBrowserPanelPluginFactory]:
    return plugin_util.get_plugin_factories("pyri.plugins.webui_browser_panel")

def get_all_webui_browser_panels_infos() -> Dict[str,Any]:
    ret = dict()
    factories = get_webui_browser_panel_factories()
    for factory in factories:
        ret[factory.get_plugin_name()] = factory.get_panels_infos()
    return ret

def get_all_webui_default_browser_panels(layout_config = "default") -> List[Tuple[PyriWebUIBrowserPanelInfo,"PyriGoldenLayoutPanelConfig"]]:
    default_panels = []
    factories = get_webui_browser_panel_factories()
    for factory in factories:
        default_panels.extend(factory.get_default_panels(layout_config))
    default_panels_sorted = sorted(default_panels, key=lambda x: x[0].priority)
    return default_panels_sorted