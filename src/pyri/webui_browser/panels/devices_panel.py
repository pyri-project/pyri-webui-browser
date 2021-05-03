from typing import List, Dict, Callable, Any
from ..plugins.panel import PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
import importlib_resources
import js
import traceback
from RobotRaconteurCompanion.Util.IdentifierUtil import IdentifierUtil
from RobotRaconteur.RobotRaconteurPythonUtil import SplitQualifiedName

from RobotRaconteur.Client import *
from .. import util

class PyriDevicesPanel(PyriWebUIBrowserPanelBase):

    def __init__(self, device_manager, core):
        self.vue = None
        self.core = core
        self.device_manager = device_manager

    def init_vue(self,vue):
        self.vue = vue

    def refresh_device_add(self, *args):
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
        ret = js.confirm(f"Remove device {dev_name}?")
        if not ret:
            return
        self.core.create_task(self.do_device_remove(dev_name))

    async def do_device_remove_selected(self,dev_names):
        try:            
            dev_manager = self.device_manager.device_manager.GetDefaultClient()
            for dev_name in dev_names:
                await dev_manager.async_remove_device(dev_name,None)
        except:
            traceback.print_exc()
            js.alert(f"Device remove failed:\n\n{traceback.format_exc()}")
        

    def device_remove_selected(self, *args):
        
        b_device_table = self.vue["$refs"].device_list
        selections = b_device_table.getSelections()
        dev_names = []
        count = len(selections)
        for i in range(count):
            t = selections[i]
            dev_names.append(t["local_name"])

        if len(dev_names) == 0:
            return

        dev_names_text = ", ".join(dev_names)
        ret = js.confirm(f"Remove devices {dev_names_text}?")
        if not ret:
            return
        self.core.create_task(self.do_device_remove_selected(dev_names))

    def implemented_types(self, local_name):
        if self.vue is None:
            return ""

        implemented_types = None
        device_infos = None

        try:
            device_infos = self.core.device_infos[local_name]
        except KeyError:
            return ""
        try:            
            implemented_types = [SplitQualifiedName(device_infos["device_info"].root_object_type)[1]]
            root_object_implements = device_infos["device_info"].root_object_implements
            if root_object_implements is not None:
                implemented_types+= [SplitQualifiedName(r)[1] for r in root_object_implements]
            
        except:
            return ""
        return ", ".join(implemented_types)
    
    async def run(self):
        await RRN.AsyncSleep(0.1,None)
        
        last_devices = set()

        device_table = []
                
        while True:
            try:
                devices_states = self.core.devices_states
                new_devices = self.core.active_device_names                
                table_updated = False
                if set(new_devices) != last_devices:
                    #TODO: Remove old code
                    # self.vue["$data"].active_device_names = js.python_to_js(new_devices)             
                    # last_devices = set(new_devices)                    
                    # for d in last_devices:
                    #     try:
                    #         self.vue["$data"].device_names[d] = devices_states.devices_states[d].device.name
                    #         self.vue["$data"].device_state_flags[d] = util.device_state_flags(devices_states, d)
                    #     except:
                    #         pass
                    last_devices = set(new_devices)
                    new_table = []
                    for d in last_devices:
                        d1 = {
                            "local_name": d,
                            "device_name": "",
                            "types": "",
                            "status": "disconnected",
                            "state_flags": "",
                            "select": False
                        }
                        
                        try:
                            d["device_name"] = devices_states.devices_states[d].device.name
                            d["device_state_flag"] = util.device_state_flags(devices_states, d)
                        except:
                            pass
                        new_table.append(d1)
                    self.vue["$data"].device_list = js.python_to_js(new_table)
                    device_table = new_table
                    table_updated = True                    
                            
                if not table_updated:
                    b_device_table = self.vue["$refs"].device_list                    

                    for i in range(len(device_table)):
                        t = device_table[i]
                        d = t["local_name"]                        
                        try:                            
                            new_status = util.device_status_name(devices_states,d)
                            if t["status"] != new_status:                                
                                b_device_table.updateCell(js.python_to_js({"index": i, "field": "status", "value": new_status}))                                
                                t["status"] = new_status
                            
                            new_flags = util.device_state_flags(devices_states, d)
                            if t["state_flags"] != new_flags:
                                b_device_table.updateCell(js.python_to_js({"index": i, "field": "state_flags", "value": new_flags}))
                                t["state_flags"] = new_flags
                        except:
                            traceback.print_exc()

                        try:
                            d_name = devices_states.devices_states[d].device.name
                            if t["device_name"] != d_name:
                                b_device_table.updateCell(js.python_to_js({"index": i, "field": "device_name", "value": d_name}))
                                t["device_name"] = d_name
                        except:
                            pass

                        try:
                            implemented_types = self.implemented_types(d)                            
                            if t["types"] != implemented_types:
                                b_device_table.updateCell(js.python_to_js({"index": i, "field": "types", "value": implemented_types}))
                                t["types"] = implemented_types
                        except:
                            traceback.print_exc()
                            pass

                        #new_flags[d] = ""
                        #new_status[d] = "error"

                #self.vue["$data"].active_device_status = js.python_to_js(new_status)
                        
                #self.vue["$data"].device_state_flags = js.python_to_js(new_flags)

            except:
                traceback.print_exc()
                self.vue["$data"].device_list = []
            
            await RRN.AsyncSleep(0.5,None)
        

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

    def register_devices_panel(container, state):
        container.getElement().html(devices_panel_html)

    core.layout.register_component("devices",register_devices_panel)

    core.layout.add_panel(panel_config)

    core.layout.add_panel_menu_item("devices", "Devices")

    devices_panel_obj = PyriDevicesPanel(core.device_manager, core)

    devices_panel = js.Vue.new(js.python_to_js({
        "el": "#active_devices_table",
        "components": {
            "BootstrapTable": js.window.BootstrapTable
        },
        "data":
        {
            "active_device_names": [],                                    
            "detected_devices": [],
            "selected_device_info": [],
            "device_list_columns":
            [
                {
                    "field": "select",
                    "checkbox": True
                },
                {
                    "title": "Local Name",
                    "field": "local_name"
                },
                {
                    "title": "Device Name",
                    "field": "device_name",
                },
                {
                    "title": "Device Types",
                    "field": "types"
                },
                {
                    "title": "Status",
                    "field": "status",
                    "formatter": lambda value,row,index,field: f"<span class=\"{'device_status_text_' + value}\"></span>"
                },
                {
                    "title": "State Flags",
                    "field": "state_flags"
                },
                {
                    "title": "Action",
                    "field": "actions",                    
                    "formatter": lambda a,b,c,d: """<a class="device_list_info" title="Device Info" @click=""><i class="fas fa-2x fa-info-circle"></i></a>&nbsp;
                                                    <a class="device_list_remove" title="Remove Device" @click="device_remove(local_name)"><i class="fas fa-2x fa-trash"></i></a>""",
                    "events":
                    {
                        "click .device_list_info": lambda e, value, row, d: devices_panel_obj.device_info(row["local_name"]),
                        "click .device_list_remove": lambda e, value, row, d: devices_panel_obj.device_remove(row["local_name"])
                    }
                }
            ],            
            "device_list_options": {
                "search": False,
                "showColumns": False,
                "showToggle": True,
                "search": True,
                "showSearchClearButton": True,
                "showRefresh": False,
                "cardView": True,
                "toolbar": "#device_list_toolbar"
            },
            "device_list": [],
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
                "search": True,
                "showSearchClearButton": True,
                "showToggle": True,
                "showColumns": False,
                "cardView": True,
                "showRefresh": False,
                "toolbar": "#add_device_toolbar"
            },
            "selected_device_options": {
                "search": True,
                "showSearchClearButton": True,
                "showToggle": True,
                "showColumns": False,
                "cardView": True,
                "showRefresh": False
            }

            
        },
        "methods":
        {
            "refresh_device_add": devices_panel_obj.refresh_device_add,
            "device_add": devices_panel_obj.device_add,
            "device_info": devices_panel_obj.device_info,
            "device_remove": devices_panel_obj.device_remove,
            "device_remove_selected": devices_panel_obj.device_remove_selected,
            "implemented_types": devices_panel_obj.implemented_types,
        }
    }))

    devices_panel_obj.init_vue(devices_panel)

    core.create_task(devices_panel_obj.run())

    return devices_panel_obj