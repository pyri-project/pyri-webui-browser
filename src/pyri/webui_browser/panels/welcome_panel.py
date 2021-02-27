from typing import List, Dict, Callable, Any
from ..plugins.panel import PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
import importlib_resources
import js

from ..util import jsbind

class PyriWelcomePanel(PyriWebUIBrowserPanelBase):

    def __init__(self):
        pass

    def init_vue(self, vue):
        self.vue =vue
        self.vue["$data"].count=20

    @jsbind
    def increment(self, js_this, evt):
        print(int(evt.target.getAttribute("data-joint")))
        self.vue["$data"].count+=1

    @jsbind
    def decrement(self, js_this, evt):
        print(int(evt.target.getAttribute("data-joint")))
        self.vue["$data"].count-=1

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
        container.getElement().html(welcome_panel_html)

    core.layout.register_component("welcome",register_welcome)

    core.layout.add_panel(panel_config)
    
    core.layout.add_panel_menu_item("welcome", "Welcome")

    welcome_panel_obj = PyriWelcomePanel()

    welcome_counter = js.Vue.new({
        "el": "#welcome_counter",
        "data": {
            "count": 10 
        },
        "methods":
        {
            "increment": welcome_panel_obj.increment,
            "decrement": welcome_panel_obj.decrement
        }
    })

    welcome_panel_obj.init_vue(welcome_counter)
   
    js.window.welcome_counter = welcome_counter
    js.window.welcome_panel_obj = welcome_panel_obj

    return welcome_panel_obj