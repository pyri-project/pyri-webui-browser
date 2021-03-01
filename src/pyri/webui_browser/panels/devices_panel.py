from typing import List, Dict, Callable, Any
from ..plugins.panel import PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
import importlib_resources
import js

from ..util import jsbind

class PyriDevicesPanel(PyriWebUIBrowserPanelBase):

    def __init__(self):
        self.vue = None

    def init_vue(self,vue):
        self.vue = vue

async def add_devices_panel(panel_type: str, core: PyriWebUIBrowser, parent_element: Any):

    assert panel_type == "devices"

    devices_panel_html = importlib_resources.read_text(__package__,"devices_panel.html")

    panel_config = {
        "type": "component",
        "componentName": "devices",
        "componentState": {},
        "title": "Devices",
        "id": "devices" 
    }

    gl = core.layout.layout

    def register_devices_panel(container, state):
        container.getElement().html(devices_panel_html)

    core.layout.register_component("devices",register_devices_panel)

    core.layout.add_panel(panel_config)

    core.layout.add_panel_menu_item("devices", "Devices")

    devices_panel_obj = PyriDevicesPanel()

    devices_panel = js.Vue.new({
        "el": "#active_devices_table",
        "store": core.vuex_store,        
    })

    devices_panel_obj.init_vue(devices_panel)

    return devices_panel_obj