import asyncio
import time
from .vue import Vue, VueComponent, vue_method, vue_data, vue_prop, vue_computed,vue_watch, vue_register_component
from typing import Dict, Any, Callable, Union
from . import PyriWebUIBrowser
import js
import traceback

class PyriVue(Vue):
    def __init__(self, core: PyriWebUIBrowser = None, el: Union["js.JsProxy",str] = None):
        self.core : PyriWebUIBrowser = core
        self._core_futures = []
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
                for f in self._core_futures:
                    try:
                        self.core.loop.call_soon(lambda: f.set_result(None))
                    except: 
                        traceback.print_exc()
                break
            assert i < 100, f"Could not find core! {type(self)}"
            i+=1
            

    def core_ready(self):
        pass

    async def wait_core(self, timeout = 2.5):

        if self.core:
            return self.core
        
        f = asyncio.Future()
        try:
            self._core_futures.append(f)
            await asyncio.wait_for(f,timeout)
            return self.core
        finally:
            self._core_futures.remove(f)

    def get_ref_core(self, ref_name, index = None ):
        return self.get_ref_pyobj(ref_name, index).core

    async def get_ref_core_wait(self, ref_name, index = None, timeout = 2.5):
        t1 = time.time()
        ref_py_obj = await self.get_ref_pyobj_wait(ref_name, index, timeout)
        t2 = time.time()
        timeout2 = timeout - (t2-t1)
        if timeout2 < 0:
            timeout2 = 0
        return await ref_py_obj.wait_core(timeout2)

    @property
    def bv_toast(self):
        return getattr(self.vue, "$bvToast")