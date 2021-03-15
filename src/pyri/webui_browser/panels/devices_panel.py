from typing import List, Dict, Callable, Any
from ..plugins.panel import PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
import importlib_resources
import js
import traceback
from RobotRaconteurCompanion.Util.IdentifierUtil import IdentifierUtil
from RobotRaconteur.RobotRaconteurPythonUtil import SplitQualifiedName

class PyriDevicesPanel(PyriWebUIBrowserPanelBase):

    def __init__(self, device_manager, core):
        self.vue = None
        self.core = core
        self.device_manager = device_manager

    def init_vue(self,vue):
        self.vue = vue

    def refresh_device_add(self, evt):
        self.core.create_task(self.do_refresh_device_add())

    async def do_refresh_device_add(self):
        try:
            dev_manager = self.device_manager.device_manager.GetDefaultClient()
            detected_devices = await dev_manager.async_getf_detected_devices(None)
            vue_devs = []
            ident_util = IdentifierUtil(client_obj=dev_manager)
            for d in detected_devices:
                d2 = {
                    "device": ident_util.IdentifierToString(d.device),
                    "parent_device": ident_util.IdentifierToString(d.parent_device),
                    "manufacturer": ident_util.IdentifierToString(d.manufacturer),
                    "model": ident_util.IdentifierToString(d.model),
                    "serial_number": d.serial_number,
                    "user_description": d.user_description,
                    "service_name": d.service_name,
                    "urls": "<br>".join(d.urls),
                    "root_object_type": d.root_object_type,
                    "root_object_implements": "<br>".join(d.root_object_implements)
                }
                vue_devs.append(d2)

            self.vue["$data"]["detected_devices"] = js.python_to_js(vue_devs)
        except:            
            traceback.print_exc()
            js.alert(f"Refresh add device failed:\n\n{traceback.format_exc()}")


    def device_add(self, evt):
        self.vue["$bvModal"].show("add-device-modal")
        self.core.create_task(self.do_refresh_device_add())

    async def do_add_device_selected(self,selected_device,local_dev_name):
        try:
            dev_manager = self.device_manager.device_manager.GetDefaultClient()
            ident_util = IdentifierUtil(client_obj=dev_manager)
            dev = ident_util.StringToIdentifier(selected_device)
            await dev_manager.async_add_device(dev,local_dev_name,[],None)

        except:            
            traceback.print_exc()
            js.alert(f"Add device failed:\n\n{traceback.format_exc()}")

    def add_device_selected(self, selected_device):
        self.vue["$bvModal"].hide("add-device-modal")
        local_dev_name = js.prompt("Enter local device name")
        self.core.create_task(self.do_add_device_selected(selected_device,local_dev_name))

    async def do_device_info(self, dev_name):
        try:
            dev_manager = self.device_manager.device_manager.GetDefaultClient()
            d = await dev_manager.async_getf_device_info(dev_name,None)
            vue_devs = []
            ident_util = IdentifierUtil(client_obj=dev_manager)
            
            d2 = {
                "device": ident_util.IdentifierToString(d.device),
                "parent_device": ident_util.IdentifierToString(d.parent_device),
                "manufacturer": ident_util.IdentifierToString(d.manufacturer),
                "model": ident_util.IdentifierToString(d.model),
                "serial_number": d.serial_number,
                "user_description": d.user_description,
                "service_name": d.service_name,
                "urls": "<br>".join(d.urls),
                "root_object_type": d.root_object_type,
                "root_object_implements": "<br>".join(d.root_object_implements)
            }
            vue_devs.append(d2)

            self.vue["$data"]["selected_device_info"] = js.python_to_js(vue_devs)
            self.vue["$bvModal"].show("device-info-modal")
        except:            
            traceback.print_exc()
            js.alert(f"Get device info failed:\n\n{traceback.format_exc()}")

    def device_info(self,  dev_name):
        self.core.create_task(self.do_device_info(dev_name))

    async def do_device_remove(self,dev_name):
        try:
            dev_manager = self.device_manager.device_manager.GetDefaultClient()
            await dev_manager.async_remove_device(dev_name,None)
        except:
            traceback.print_exc()
            js.alert(f"Device remove failed:\n\n{traceback.format_exc()}")
        

    def device_remove(self, dev_name):
        self.core.create_task(self.do_device_remove(dev_name))

    def implemented_types(self, local_name):
        if self.vue is None:
            return ""

        implemented_types = None
        device_infos = None

        try:
            device_infos = self.vue["$store"].state.device_infos[local_name]
        except KeyError:
            return ""
        try:            
            implemented_types = [SplitQualifiedName(device_infos.device_info.root_object_type)[1]]
            root_object_implements = device_infos.device_info.root_object_implements
            if root_object_implements is not None:
                implemented_types+= [SplitQualifiedName(r)[1] for r in root_object_implements]
            
        except:
            return ""
        return ", ".join(implemented_types)

    def device_state_flags(self, local_name):
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

    def device_name(self, local_name):
        try:
            return self.vue["$store"].state.devices_states.devices_states[local_name].device.name
        except KeyError:
            return ""
        except AttributeError:
            return ""

    def device_connected(self, local_name):
        try:
            return self.vue["$store"].state.devices_states.devices_states[local_name].connected
        except KeyError:
            return ""
        except AttributeError:
            return ""

    def device_ready(self, local_name):
        try:
            return self.vue["$store"].state.devices_states.devices_states[local_name].ready
        except KeyError:
            return ""
        except AttributeError:
            return ""

    def device_error(self, local_name):
        try:
            return self.vue["$store"].state.devices_states.devices_states[local_name].error
        except KeyError:
            return ""
        except AttributeError:
            return ""
        

async def add_devices_panel(panel_type: str, core: PyriWebUIBrowser, parent_element: Any):

    assert panel_type == "devices"

    devices_panel_html = importlib_resources.read_text(__package__,"devices_panel.html")

    panel_config = {
        "type": "component",
        "componentName": "devices",
        "componentState": {},
        "title": "Devices",
        "id": "devices",
        "isClosable": False
    }

    gl = core.layout.layout

    def register_devices_panel(container, state):
        container.getElement().html(devices_panel_html)

    core.layout.register_component("devices",register_devices_panel)

    core.layout.add_panel(panel_config)

    core.layout.add_panel_menu_item("devices", "Devices")

    devices_panel_obj = PyriDevicesPanel(core.device_manager, core)

    devices_panel = js.Vue.new(js.python_to_js({
        "el": "#active_devices_table",
        "store": core.vuex_store,
        "components": {
            "BootstrapTable": js.window.BootstrapTable
        },
        "data":
        {
            "detected_devices": [],
            "selected_device_info": [],
            "add_device_columns": [
                {
                    "title": "Device",
                    "field": "device"
                },
                {
                    "title": "Parent Device",
                    "field": "parent_device",                    
                },
                {
                    "title": "Manufacturer",
                    "field": "manufacturer"
                },
                {
                    "title": "Model",
                    "field": "model"
                },
                {
                    "title": "Serial Number",
                    "field": "serial_number"
                },
                {
                    "title": "User Description",
                    "field": "user_description"
                },
                {
                    "title": "Service Name",
                    "field": "service_name"
                },
                {
                    "title": "URLs",
                    "field": "urls"
                },
                {
                    "title": "Root Object Type",
                    "field": "root_object_type"                    
                },
                {
                    "title": "Root Object Implements",
                    "field": "root_object_implements"
                },
                {
                    "title": "Action",
                    "field": "action",
                    "formatter": lambda a,b,c,d: '<a href="javascript:" class="device_panel_add_device"><i class="fas fs-4x fa-plus-circle"></i></a>',
                    "events":
                    {
                        "click .device_panel_add_device": lambda e, value, row, d: devices_panel_obj.add_device_selected(row["device"])
                    }
                    
                }
            ],
            "selected_device_info_columns": [
                {
                    "title": "Device",
                    "field": "device"
                },
                {
                    "title": "Parent Device",
                    "field": "parent_device",                    
                },
                {
                    "title": "Manufacturer",
                    "field": "manufacturer"
                },
                {
                    "title": "Model",
                    "field": "model"
                },
                {
                    "title": "Serial Number",
                    "field": "serial_number"
                },
                {
                    "title": "User Description",
                    "field": "user_description"
                },
                {
                    "title": "Service Name",
                    "field": "service_name"
                },
                {
                    "title": "URLs",
                    "field": "urls"
                },
                {
                    "title": "Root Object Type",
                    "field": "root_object_type"                    
                },
                {
                    "title": "Root Object Implements",
                    "field": "root_object_implements"
                }
            ],
            "add_device_options": {
                "search": False,
                "showColumns": True,
                "cardView": True,
                "height": 460
            }
            
        },
        "methods":
        {
            "refresh_device_add": devices_panel_obj.refresh_device_add,
            "device_add": devices_panel_obj.device_add,
            "device_info": devices_panel_obj.device_info,
            "device_remove": devices_panel_obj.device_remove,
            "implemented_types": devices_panel_obj.implemented_types,
            "device_state_flags": devices_panel_obj.device_state_flags,
            "device_name": devices_panel_obj.device_name,
            "device_connected": devices_panel_obj.device_connected,
            "device_error": devices_panel_obj.device_error,
            "device_ready": devices_panel_obj.device_ready,
        }
    }))

    devices_panel_obj.init_vue(devices_panel)

    return devices_panel_obj