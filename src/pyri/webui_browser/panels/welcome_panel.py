from typing import List, Dict, Callable, Any
from ..plugins.panel import PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
import importlib_resources


class PyriWelcomePanel(PyriWebUIBrowserPanelBase):
    pass

async def add_welcome_panel(panel_type: str, core: PyriWebUIBrowser, parent_element: Any):
    assert panel_type == "welcome"

    welcome_panel_html = importlib_resources.read_text(__package__,"welcome_panel.html")

    panel_config = {
        "type": "component",
        "componentName": "welcome",
        "componentState": {},
        "title": "Welcome",
        "id": "welcome" 
    }

    gl = core.layout.layout

    def register_welcome(container, state):
        print(welcome_panel_html)
        container.getElement().html(welcome_panel_html)

    welcome_panel_obj = PyriWelcomePanel()

    core.layout.register_component("welcome",register_welcome)

    core.layout.add_panel(panel_config)
    
    core.layout.add_panel_menu_item("welcome", "Welcome")

    return welcome_panel_obj