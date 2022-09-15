from .pyri_vue import PyriVue, vue_data, vue_method
import time
import importlib_resources
from .util import to_js2
import js
import traceback

class PyriWebUICoreAppVue(PyriVue):
    def __init__(self, core ,el, *args, **kwargs):
        super().__init__(core, el, *args, **kwargs)

    vue_template = importlib_resources.read_text(__package__,"pyri_core_app.html")

    core_components = vue_data(to_js2([]))

    async def add_component(self, component_type, component_ref, component_info = {}, component_index = -1, timeout = 2.5):
        component_dict = to_js2({
            "component_type": component_type,
            "component_ref": component_ref,
            "component_info": to_js2(component_info)
        })

        if component_index < 0:
            self.core_components.push(component_dict)
        else:
            self.core_components.splice(component_index, 0, component_dict)

        return await self.get_ref_pyobj_wait(component_ref, index = 0, timeout = timeout)
