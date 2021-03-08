from typing import List, Dict, Callable, Any
from ..plugins.panel import PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
import importlib_resources
import js
import traceback

class PyriProgramPanel(PyriWebUIBrowserPanelBase):

    def __init__(self, core, device_manager):
        self.vue = None
        self.core = core
        self.device_manager = device_manager

    def init_vue(self,vue):
        self.vue = vue

    async def do_procedure_run(self, name):
        try:
            c = self.device_manager.get_device_subscription("sandbox").GetDefaultClient()
            gen = await c.async_execute_procedure(name, [], None)

            res = await gen.AsyncNext(None,None)
            await gen.AsyncClose(None)

            res_printed = '\n'.join(res.printed)
            js.window.alert(f"Run procedure {name} complete:\n\n{res_printed}")
            
        except Exception as e:
            
            js.window.alert(f"Run procedure {name} failed:\n\n{traceback.format_exc()}" )

    def procedure_run(self, name):
        self.core.create_task(self.do_procedure_run(name))

    def procedure_open(self, name):
        js.window.alert(f"Procedure open: {name}")

    def procedure_copy(self, name):
        js.window.alert(f"Procedure copy: {name}")

    def procedure_info(self, name):
        js.window.alert(f"Procedure info: {name}")

    def procedure_delete(self, dev_name):
        js.window.confirm(f"Remove device: {dev_name}?")

    async def do_refresh_procedure_table(self):
        
        db = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()

        res = await db.async_filter_variables("procedure", "", ["blockly","pyri"], None)

        procedures = []
        for r in res:
            try:
                tags = await db.async_getf_variable_tags("procedure", r, None)
                doc = await db.async_getf_variable_doc("procedure", r, None)
                procedure_info = {
                        "procedure_name": r,
                        "docstring": doc,
                        "modified": ""
                    }

                if "blockly" in tags:
                    procedure_info["procedure_type"] = "Blockly"
                elif "pyri" in tags:
                    procedure_info["procedure_type"] = "PyRI"
                procedures.append(
                    procedure_info
                )  
            except:
                traceback.print_exc()
                procedures.append(
                    {
                        "procedure_name": r,
                        "procedure_type": "Unknown",
                        "docstring": "",
                        "modified": "Unknown"
                    }
                )        

        if self.vue is not None:
            self.vue["$data"].procedures = procedures


    def refresh_procedure_table(self, *args):
        self.core.create_task(self.do_refresh_procedure_table())

        

async def add_program_panel(panel_type: str, core: PyriWebUIBrowser, parent_element: Any):

    assert panel_type == "program"

    program_panel_html = importlib_resources.read_text(__package__,"program_panel.html")

    panel_config = {
        "type": "component",
        "componentName": "program",
        "componentState": {},
        "title": "Program",
        "id": "program" 
    }

    gl = core.layout.layout

    def register_program_panel(container, state):
        container.getElement().html(program_panel_html)

    core.layout.register_component("program",register_program_panel)

    core.layout.add_panel(panel_config)

    core.layout.add_panel_menu_item("program", "Program")

    program_panel_obj = PyriProgramPanel(core, core.device_manager)

    program_panel = js.Vue.new({
        "el": "#procedures_table",
        "store": core.vuex_store,
        "data":
        {
            "procedures": []
        },
        "methods":
        {
            "procedure_run": program_panel_obj.procedure_run,
            "procedure_open": program_panel_obj.procedure_open,
            "procedure_copy": program_panel_obj.procedure_copy,
            "procedure_info": program_panel_obj.procedure_info,
            "procedure_delete": program_panel_obj.procedure_delete,
            "refresh_procedure_table": program_panel_obj.refresh_procedure_table
        }
    })

    program_panel_obj.init_vue(program_panel)

    return program_panel_obj