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

        js.console.log(self.core_components)

        t1 = time.time()

        while True:
            if time.time() - t1 > timeout:
                raise TimeoutError(f"Timed out waiting for component {component_ref} to mount")

            try:
                return self.get_ref_pyobj(component_ref, 0)
            except AttributeError:
                #traceback.print_exc()
                pass

            await self.next_tick()