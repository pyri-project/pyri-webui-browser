from .vue import Vue, VueComponent, vue_method, vue_data, vue_prop, vue_computed
from typing import Dict, Any, Callable, Union
from . import PyriWebUIBrowser
import js
import traceback

class PyriVue(Vue):
    def __init__(self, core: PyriWebUIBrowser = None, el: Union["js.JsProxy",str] = None, components: Dict[str,"js.JsProxy"] = {}):
        self.core = core
        super().__init__(el,components)

    def mounted(self):
        super().mounted()

        if not hasattr(self, "core") or self.core is None:
            try:
                self.core = getattr(self.vue,"$parent").py_obj.core
            except:
                traceback.print_exc()