from .vue import Vue, VueComponent, vue_method, vue_data, vue_prop, vue_computed,vue_watch
from typing import Dict, Any, Callable, Union
from . import PyriWebUIBrowser
import js
import traceback

class PyriVue(Vue):
    def __init__(self, core: PyriWebUIBrowser = None, el: Union["js.JsProxy",str] = None):
        self.core = core
        super().__init__(el)

    def mounted(self):
        super().mounted()
        
        if getattr(self, "core", None) is None:
            self._vue_create_task(self._vue_find_core())

    async def _vue_find_core(self):
        i = 0
        while True:            
            await self.next_tick()         
            if getattr(self, "core", None) is not None:
                break
            
            self.core = getattr(getattr(self.vue,"$parent").py_obj,"core",None)
            if self.core is not None:
                try:
                    self.core_ready()
                except:
                    traceback.print_exc()
                break
            assert i < 100, f"Could not find core! {type(self)}"
            i+=1
            

    def core_ready(self):
        pass