from typing import List, Dict, Callable, Any
from ..plugins.panel import PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
import importlib_resources
import js
from RobotRaconteur.Client import *
import traceback

class PyriWelcomePanel(PyriWebUIBrowserPanelBase):

    def __init__(self,core):
        self.vue = None
        self.core = core

    def init_vue(self, vue):
        self.vue =vue
        self.vue["$data"].count=20

    
    def increment(self,  evt):
        print(int(evt.target.getAttribute("data-joint")))
        self.vue["$data"].count+=1

    
    def decrement(self, evt):
        print(int(evt.target.getAttribute("data-joint")))
        self.vue["$data"].count-=1

    
    async def run(self):
        last_seqno = -1
        last_devices = set()
        while True:
            try:
                devices_states = self.core.devices_states
                if devices_states is not None:
                    new_seqno = self.core.devices_states.seqno
                    if new_seqno != last_seqno:
                        self.vue["$data"].seqno = new_seqno
                        last_seqno = new_seqno
            except:
                traceback.print_exc()
                self.vue["$data"].seqno = -1
            try:
                new_devices = self.core.active_device_names
                if set(new_devices) != last_devices:
                    self.vue["$data"].active_device_names = new_devices
                    last_devices = set(new_devices)
            except:
                traceback.print_exc()
                self.vue["$data"].active_device_names = []
            await RRN.AsyncSleep(0.05,None)
        
        

async def add_welcome_panel(panel_type: str, core: PyriWebUIBrowser, parent_element: Any):
    assert panel_type == "welcome"

    welcome_panel_html = importlib_resources.read_text(__package__,"welcome_panel.html")

    panel_config = {
        "type": "component",
        "componentName": "welcome",
        "componentState": {},
        "title": "Welcome",
        "id": "welcome",
        "isClosable": False
    }

    gl = core.layout.layout

    def register_welcome(container, state):
        container.getElement().html(welcome_panel_html)

    core.layout.register_component("welcome",register_welcome)

    core.layout.add_panel(panel_config)
    
    core.layout.add_panel_menu_item("welcome", "Welcome")

    welcome_panel_obj = PyriWelcomePanel(core)

    welcome_counter = js.Vue.new(js.python_to_js({
        "el": "#welcome_counter",
        "data": {
            "count": 10,
            "seqno": -1,
            "active_device_names": []
        },
        "methods":
        {
            "increment": welcome_panel_obj.increment,
            "decrement": welcome_panel_obj.decrement
        }       
    }))

    welcome_panel_obj.init_vue(welcome_counter)
   
    core.create_task(welcome_panel_obj.run())

    return welcome_panel_obj