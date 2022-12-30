import importlib_resources
from RobotRaconteur.Client import *
from .. import util
from ..util import to_js2
import js
import traceback

from ..pyri_vue import PyriVue, VueComponent, vue_register_component, vue_data, vue_method
from .procedure_util import run_procedure, stop_all_procedure, new_blockly_procedure, do_stop_all
import json

@VueComponent
class PyriProcedureListComponent(PyriVue):

    vue_template = importlib_resources.read_text(__package__,"procedure_list_component.html")

    vue_components = {
        "BootstrapTable": js.window.BootstrapTable
    }

    procedures = vue_data(lambda: [])

    procedures_columns = vue_data(lambda vue: 
        [
            {
                "field": "select",
                "checkbox": True
            },
            {
                "field": "procedure_name",
                "title": "Name"
            },
            {
                "field": "procedure_type",
                "title": "Type"
            },
            {
                "field": "docstring",
                "title": "Docstring"
            },
            {
                "field": "modified",
                "title": "Modified"
            },
            {
                "field": "actions",
                "title": "Actions",
                "searchable": False,
                "formatter": lambda a,b,c,d: """<a class="procedure_list_play" title="Run Procedure"><i class="fas fa-2x fa-play"></i></a>&nbsp;
                                                <a class="procedure_list_open" title="Open Procedure"><i class="fas fa-2x fa-folder-open"></i></a>&nbsp;
                                                <a class="procedure_list_copy" title="Copy Procedure"><i class="fas fa-2x fa-copy"></i></a>&nbsp;
                                                <a class="procedure_list_info" title="Procedure Info"><i class="fas fa-2x fa-info-circle"></i></a>&nbsp;
                                                <a class="procedure_list_remove" title="Delete Procedure"><i class="fas fa-2x fa-trash"></i></a>""",
                "events": {
                    "click .procedure_list_play": js.Function.new("vue_this", "return (function (e, value, row, d) { vue_this.procedure_run(row.procedure_name); })")(vue),
                    "click .procedure_list_open": js.Function.new("vue_this", "return (function (e, value, row, d) { vue_this.procedure_open(row.procedure_name); })")(vue),
                    "click .procedure_list_copy": js.Function.new("vue_this", "return (function (e, value, row, d) { vue_this.procedure_copy(row.procedure_name); })")(vue),
                    "click .procedure_list_info": js.Function.new("vue_this", "return (function (e, value, row, d) { vue_this.procedure_info(row.procedure_name); })")(vue),
                    "click .procedure_list_remove": js.Function.new("vue_this", "return (function (e, value, row, d) { vue_this.procedure_delete(row.procedure_name); })")(vue)
                }
            }
        ]
    )

    procedures_list_options = vue_data(lambda:
        {
            "search": True,
            "showColumns": False,
            "showToggle": True,
            "search": True,
            "showSearchClearButton": True,
            "showRefresh": False,
            "cardView": True,
            "toolbar": "#procedure_list_toolbar"
        }
    )

    def __init__(self):
        super().__init__()

    @vue_method
    def procedure_run(self, name):
        self.core.create_task(run_procedure(self.core.device_manager,name,self))

    @vue_method
    async def procedure_open(self,name):
        try:
            var_storage = self.core.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            tags = await var_storage.async_getf_variable_tags("procedure",name,None)
            if "pyri" in tags:
                from .procedure_pyri_component import open_pyri_editor_panel
                await open_pyri_editor_panel(self.core, name)
            elif "blockly" in tags:
                from .procedure_blockly_component import open_blockly_editor_panel
                await open_blockly_editor_panel(self.core, name)
            else:
                raise RR.InvalidArgumentException("Procedure is not a Blockly or PyRI procedure!")
        except:
            js.alert(f"Open procedure failed:\n\n{traceback.format_exc()}")

    @vue_method
    async def procedure_copy(self,name):
        copy_name = js.prompt("Procedure copy name")
        try:

            var_storage = self.core.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            var_consts = RRN.GetConstants('tech.pyri.variable_storage', var_storage)
            variable_persistence = var_consts["VariablePersistence"]
            variable_protection_level = var_consts["VariableProtectionLevel"]
            procedure = await var_storage.async_getf_variable_value("procedure",name,None)
            tags = await var_storage.async_getf_variable_tags("procedure",name,None)
            doc = await var_storage.async_getf_variable_doc("procedure",name,None)
            await var_storage.async_add_variable2("procedure", copy_name ,"string", \
                procedure, tags, {}, variable_persistence["const"], None, variable_protection_level["read_write"], \
                    [], doc, False, None)
        except:
            traceback.print_exc()

    @vue_method
    def procedure_info(self, name):
        js.window.alert(f"Procedure info: {name}")

    @vue_method
    async def procedure_delete(self,name):    
        if not js.window.confirm(f"Delete procedure: {name}?"):
            return
            
        try:
            var_storage = self.core.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            await var_storage.async_delete_variable("procedure", name, None)
        except:
            traceback.print_exc()

    @vue_method
    async def procedure_delete_selected(self, *args):
        b_procedure_table = self.refs.procedures_list
        selections = b_procedure_table.getSelections()
        names = []
        count = len(selections)
        for i in range(count):
            t = selections[i]
            names.append(t.procedure_name)

        if len(names) == 0:
            return

        dev_names_text = ", ".join(names)
        ret = js.confirm(f"Delete procedures {dev_names_text}?")
        if not ret:
            return
        
        try:
            var_storage = self.core.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            for name in names:
                await var_storage.async_delete_variable("procedure", name, None)
        except:
            traceback.print_exc()

    @vue_method
    async def refresh_procedure_table(self, *args):
        try:
        
            db = self.core.device_manager.get_device_subscription("variable_storage").GetDefaultClient()

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
            
            self.procedures = to_js2(procedures)
        except:
            traceback.print_exc()

    @vue_method
    async def new_blockly_procedure(self, *args):
        try:
            procedure_name = js.prompt("New procedure name")
            procedure_json = json.dumps(new_blockly_procedure(procedure_name, ""))
            variable_manager = self.core.device_manager.get_device_subscription("variable_storage").GetDefaultClient()

            var_consts = RRN.GetConstants('tech.pyri.variable_storage', variable_manager)
            variable_persistence = var_consts["VariablePersistence"]
            variable_protection_level = var_consts["VariableProtectionLevel"]

            await variable_manager.async_add_variable2("procedure", procedure_name ,"string", \
            RR.VarValue(procedure_json,"string"), ["blockly"], {}, variable_persistence["const"], None, variable_protection_level["read_write"], \
                [], "User defined procedure", False, None)

            from .procedure_blockly_component import open_blockly_editor_panel
            await open_blockly_editor_panel(self.core, procedure_name)

        except:
            traceback.print_exc()

    @vue_method
    async def new_pyri_procedure(self, *args):
        try:
            procedure_name = js.prompt("New procedure name")
            pyri_src = f"def {procedure_name}():\n    pass"
            variable_manager = self.core.device_manager.get_device_subscription("variable_storage").GetDefaultClient()

            var_consts = RRN.GetConstants('tech.pyri.variable_storage', variable_manager)
            variable_persistence = var_consts["VariablePersistence"]
            variable_protection_level = var_consts["VariableProtectionLevel"]

            await variable_manager.async_add_variable2("procedure", procedure_name ,"string", \
            RR.VarValue(pyri_src,"string"), ["pyri"], {}, variable_persistence["const"], None, variable_protection_level["read_write"], \
                [], "User defined procedure", False, None)

            from .procedure_pyri_component import open_pyri_editor_panel
            await open_pyri_editor_panel(self.core, procedure_name)

        except:
            traceback.print_exc()

    @vue_method
    def stop_all(self, evt):
        do_stop_all(self.core,self.core.device_manager)


def register_vue_components():
    vue_register_component("pyri-procedure-list", PyriProcedureListComponent)