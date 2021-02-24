from typing import List, Dict, Callable, Any
from ..plugins.panel import PyriWebUIBrowserPanelInfo, PyriWebUIBrowserPanelPluginFactory, PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
from .welcome_panel import add_welcome_panel

_panel_infos = {
    "welcome": PyriWebUIBrowserPanelInfo(
        title="Welcome",
        panel_type="welcome",
        priority=0
    )
}

class PyriStandardPanelsWebUIBrowserPanelPluginFactory(PyriWebUIBrowserPanelPluginFactory):
    def __init__(self):
        super().__init__()

    def get_plugin_name(self) -> str:
        return "pyri-webui-browser"

    def get_panels_infos(self) -> Dict[str,PyriWebUIBrowserPanelInfo]:
        return _panel_infos

    async def add_panel(self, panel_type: str, core: PyriWebUIBrowser, parent_element: Any) -> PyriWebUIBrowserPanelBase:
        if panel_type == "welcome":
            return await add_welcome_panel(panel_type, core, parent_element)
        assert False, f"Unknown panel_type \"{panel_type}\" specified"

def get_webui_browser_panel_factory():
    return PyriStandardPanelsWebUIBrowserPanelPluginFactory()