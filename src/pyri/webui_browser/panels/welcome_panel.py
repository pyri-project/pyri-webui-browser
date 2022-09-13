from typing import List, Dict, Callable, Any
from ..plugins.panel import PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
import importlib_resources
import js
from RobotRaconteur.Client import *
import traceback
from ..util import to_js2
from pyodide import create_proxy, to_js2
from ..pyri_vue import PyriVue, VueComponent

@VueComponent
class PyriWelcomePanel(PyriVue):

    vue_template = importlib_resources.read_text(__package__,"welcome_panel.html")

    def __init__(self):
        super().__init__()

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

    welcome_counter_args = to_js2({
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
    })

    js.console.log(welcome_counter_args)

    welcome_counter = js.Vue.new(welcome_counter_args)

    welcome_panel_obj.init_vue(welcome_counter)
   
    core.create_task(welcome_panel_obj.run())

    return welcome_panel_obj