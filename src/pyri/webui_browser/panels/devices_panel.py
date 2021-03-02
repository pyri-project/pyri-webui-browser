from typing import List, Dict, Callable, Any
from ..plugins.panel import PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
import importlib_resources
import js
import traceback

from ..util import jsbind

class PyriDevicesPanel(PyriWebUIBrowserPanelBase):

    def __init__(self):
        self.vue = None

    def init_vue(self,vue):
        self.vue = vue

    @jsbind
    def device_info(self, js_this, dev_name):
        js.window.alert(f"Device info: {dev_name}")

    @jsbind
    def device_remove(self, js_this, dev_name):
        js.window.confirm(f"Remove device: {dev_name}?")

    @jsbind
    def implemented_types(self, js_this, local_name):
        if self.vue is None:
            return ""

        implemented_types = None
        device_infos = None

        try:
            device_infos = self.vue["$store"].state.device_infos[local_name]
        except KeyError:
            return ""
        try:            
            implemented_types = [device_infos.device_info.root_object_type]
            root_object_implements = device_infos.device_info.root_object_implements
            if root_object_implements is not None:
                implemented_types+= root_object_implements
            
        except:
            return ""
        return " ".join(implemented_types)

    @jsbind
    def device_state_flags(self, js_this, local_name):
        if self.vue is None:
            return ""
        
        state_flags = []
        try:
            typed_device_states = self.vue["$store"].state.devices_states.devices_states[local_name].state
        except KeyError:
            return ""

        if typed_device_states is None:
            return ""

        for v in typed_device_states:
            f = v.display_flags
            if f is not None:
                state_flags.extend(f)

        return " ".join(state_flags)
        

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
        "methods":
        {
            "device_info": devices_panel_obj.device_info,
            "device_remove": devices_panel_obj.device_remove,
            "implemented_types": devices_panel_obj.implemented_types,
            "device_state_flags": devices_panel_obj.device_state_flags
        }
    })

    devices_panel_obj.init_vue(devices_panel)

    return devices_panel_obj