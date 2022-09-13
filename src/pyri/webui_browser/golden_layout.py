import js
import json
from .util import to_js2
from pyodide import create_proxy
from .pyri_vue import PyriVue, VueComponent, vue_data, vue_prop
import traceback

_golden_layout_config = {
    "settings":{
        "hasHeaders": True,
        "constrainDragToContainer": True,
        "reorderEnabled": True,
        "selectionEnabled": False,
        "popoutWholeStack": False,
        "blockedPopoutsThrowError": True,
        "closePopoutsOnUnload": True,
        "showPopoutIcon": False, 
        "showMaximiseIcon": True,
        "showCloseIcon": False
    },
    "dimensions": 
    {
        "borderWidth": 15,
        "minItemHeight": 10,
        "minItemWidth": 10,
        "headerHeight": 30,
        "dragProxyWidth": 300,
        "dragProxyHeight": 200
    },
    "labels": 
    {
        "close": 'close',
        "maximise": 'maximise',
        "minimise": 'minimise',
        "popout": 'open in new window'
    },
    "root":
    {
        "type": "stack",
        "isClosable": False
    },
    "header":
    {
        "popout": False,
        "popin": False,
        "close": True
    }
}

_gl_template = """<div ref="goldenlayout_root" style="position: absolute; width: 100%; height: 100%"></div>"""

#https://github.com/chyj4747/vue3-golden-layout-virtualcomponent/blob/980fdc1f153671fb81502dc7412e5b3c52c1211d/src/components/Glayout.vue

@VueComponent(register="pyri-golden-layout")
class PyriGoldenLayout(PyriVue):

    vue_template = _gl_template

    info = vue_prop()

    def __init__(self):
        super().__init__()
        self._layout = None
        self._on_resize_proxy = None

    def mounted(self):
        print("golden layout mounted")
        super().mounted()
        
        layoutContainer = getattr(self.vue,"$el")
        js.console.log(layoutContainer)
        self._layout =js.goldenLayout.VirtualLayout.new(
            layoutContainer,
            create_proxy(self._bind_component_event_listener),
            create_proxy(self._unbind_component_event_listener)
        )
        js.console.log(self._layout)
        self._layout.loadLayout(to_js2(_golden_layout_config))


        #self._layout.init()

        #js.jQuery(js.window).resize(create_proxy(lambda _: self._layout.updateSize()))

        self._on_resize_proxy = create_proxy(self._on_resize)
        js.window.addEventListener("resize", self._on_resize_proxy, to_js2({"passive": True}))

        self._layout.addComponent("test-panel", to_js2({ "refId": 0}), "Test Panel")
        self._layout.addComponent("test-panel2", to_js2({ "refId": 1}), "Test Panel 2")
        js.console.log(self._layout.saveLayout())

    def before_destroy(self):
        super().before_destroy()

        js.window.removeEventListener("resize", self._on_resize_proxy)

    def _on_resize(self, evt):
        try:
            el = getattr(self.vue,"$el")
            width = el.offsetWidth
            height = el.offsetHeight
            self._layout.setSize(width, height)
        except:
            traceback.print_exc()
        
    def _bind_component_event_listener(self, container, item_config):
        print("_bind_component_event_handler")
        js.console.log(container)
        js.console.log(item_config)

        return to_js2({"component": {}, "virtual": True })

    def _unbind_component_event_listener(self, container):
        print("_unbind_component_event_handler")
        js.console.log(container)

    def _handle_container_virtual_recting_requiredEvent(self, container, width, height):
        pass

    def _handle_container_virtual_visibility_change_required_event(self, container, visible):
        pass

    def _handle_container_virtual_z_index_change_required_event(self, container, logical_z_index, default_z_index):
        pass

    @property
    def layout(self):
        return self._layout

    def register_component(self,name,constructor_function,py_this=None):
        js.golden_layout_register_component(self._layout,name,create_proxy(constructor_function),py_this)

        

    def add_panel(self,panel_config):
        self._layout.root.contentItems[0].addChild(to_js2(panel_config))

    def select_panel(self, panel_id):
        p = self._layout.root.contentItems[0].getItemsById(panel_id)
        if len(p) > 0:
            p[0].parent.setActiveContentItem(p[0])

