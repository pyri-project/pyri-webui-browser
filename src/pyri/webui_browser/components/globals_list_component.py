import importlib_resources
from RobotRaconteur.Client import *
from .. import util
from ..util import to_js2
import js
import traceback

from ..pyri_vue import PyriVue, VueComponent, vue_register_component, vue_data, vue_method
from .procedure_util import run_procedure, stop_all_procedure, new_blockly_procedure, do_stop_all
import json
import re

@VueComponent
class PyriGlobalsListComponent(PyriVue):

    vue_template = importlib_resources.read_text(__package__,"globals_list_component.html")

    vue_components = {
        "BootstrapTable": js.window.BootstrapTable
    }

    variables = vue_data(lambda: [])

    variables_columns = vue_data(lambda vue: 
        [
            {
                "field": "select",
                "checkbox": True
            },
            {
                "field": "variable_name",
                "title": "Name"
            },
            {
                "field": "docstring",
                "title": "Docstring"
            },
            {
                "field": "data_type",
                "title": "Data Type"
            },
            {
                "field": "tags",
                "title": "Tags"
            },
            {
                "field": "modified",
                "title": "Modified"
            },
            {
                "field": "actions",
                "title": "Actions",
                "searchable": False,
                "formatter": lambda a,b,c,d: """
                                            <a class="globals_table_open" title="Open Variable"><i class="fas fa-2x fa-folder-open"></i></a>&nbsp;
                                            <a class="globals_table_copy" title="Copy Variable"><i class="fas fa-2x fa-copy"></i></a>&nbsp;
                                            <a class="globals_table_info" title="Variable Info"><i class="fas fa-2x fa-info-circle"></i></a>&nbsp;
                                            <a class="globals_table_remove" title="Delete Variable"><i class="fas fa-2x fa-trash"></i></a>
                                            """,
                "events": {
                    "click .globals_table_open": js.Function.new("vue_this", "return (function (e, value, row, d) { vue_this.variable_open(row.variable_name); })")(vue),
                    "click .globals_table_copy": js.Function.new("vue_this", "return (function (e, value, row, d) { vue_this.variable_copy(row.variable_name); })")(vue),
                    "click .globals_table_info": js.Function.new("vue_this", "return (function (e, value, row, d) { vue_this.variable_info(row.variable_name); })")(vue),
                    "click .globals_table_remove": js.Function.new("vue_this", "return (function (e, value, row, d) { vue_this.variable_delete(row.variable_name); })")(vue)
                }
            }
        ]
    )

    new_variable_type_selectedState = vue_data(lambda: "")
    new_variable_type_selected = vue_data(lambda: "")
    new_variable_name_inputState = vue_data(lambda: "")
    new_variable_name = vue_data(lambda: "")
    new_variable_type_select_options = vue_data(lambda: [])

    variables_options = vue_data(lambda:
        {
            "search": True,
            "showColumns": False,
            "showToggle": True,
            "search": True,
            "showSearchClearButton": True,
            "showRefresh": False,
            "cardView": True,
            "toolbar": "#variables_toolbar"
        }
    )

    def __init__(self):
        super().__init__()

    @vue_method
    def variable_open(self, name):
        js.alert("Variable open")
        #p = PyriBlocklyProgramPanel(name,self.core,self.device_manager)


    @vue_method
    async def variable_copy(self,name):
        copy_name = js.prompt("Variable copy name")
        if not copy_name:
            return
        try:

            var_storage = self.core.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            var_consts = RRN.GetConstants('tech.pyri.variable_storage', var_storage)
            variable_persistence = var_consts["VariablePersistence"]
            variable_protection_level = var_consts["VariableProtectionLevel"]
            procedure = await var_storage.async_getf_variable_value("globals",name,None)
            tags = await var_storage.async_getf_variable_tags("globals",name,None)
            doc = await var_storage.async_getf_variable_doc("globals",name,None)
            await var_storage.async_add_variable2("globals", copy_name ,"string", \
                procedure, tags, {}, variable_persistence["normal"], None, variable_protection_level["read_write"], \
                    [], doc, False, None)
        except:
            traceback.print_exc()

    @vue_method
    def variable_info(self, name):
        js.window.alert(f"Variable info: {name}")

    @vue_method
    async def variable_delete(self,name):
        if not js.window.confirm(f"Delete global variable: \"{name}\"?"):       
            return
        try:
            var_storage = self.core.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            await var_storage.async_delete_variable("globals", name, None)
        except:
            pass

    @vue_method
    async def variable_delete_selected(self, *args):
        
        b_globals_table = self.refs.globals_list
        selections = b_globals_table.getSelections()
        names = []
        count = len(selections)
        for i in range(count):
            t = selections[i]
            names.append(t.variable_name)

        if len(names) == 0:
            return

        names_text = ", ".join(names)
        ret = js.confirm(f"Delete variables {names_text}?")
        if not ret:
            return

        try:
            var_storage = self.core.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            for name in names:
                await var_storage.async_delete_variable("globals", name, None)
        except:
            pass

    @vue_method
    async def refresh_globals_table(self, *args):
        try:
        
            db = self.core.device_manager.get_device_subscription("variable_storage").GetDefaultClient()

            res = await db.async_filter_variables("globals", "", [], None)

            vars = []
            for r in res:
                try:
                    var_info = await db.async_getf_variable_info("globals", r, None)
                    doc = await db.async_getf_variable_doc("globals", r, None)
                    var_info2 = {
                            "variable_name": r,
                            "docstring": doc,
                            "data_type": var_info.datatype,
                            "tags": " ".join(var_info.tags),
                            "modified": ""
                        }

                    vars.append(
                        var_info2
                    )  
                except:
                    traceback.print_exc()
                    vars.append(
                        {
                            "variable_name": r,
                            "docstring": "",
                            "data_type": "Unknown",
                            "tags": "",
                            "modified": "Unknown"
                        }
                    )        

            self.variables = to_js2(vars)
        except:
            traceback.print_exc()

    @vue_method
    def new_variable(self, *args):
        try:
            self.reset_new_variable()
            
            self.bv_modal.show("new_variable_modal")
        except:
            traceback.print_exc()

    @vue_method
    def reset_new_variable(self, *args):
        from ..plugins.variable_dialog import get_all_webui_browser_variable_dialog_infos
        dialog_infos = get_all_webui_browser_variable_dialog_infos()

        select_values=[]
        for d1 in dialog_infos.values():
            for d2 in d1.values():
                v = ",".join([d2.variable_type] + d2.variable_tags)
                select_values.append({"value": v, "text": d2.display_name})

        self.new_variable_type_select_options = to_js2(select_values)
        if len(select_values) > 0:
            self.new_variable_type_selected = select_values[0]["value"]
        self.new_variable_name = ""        

    
    @vue_method
    def handle_submit(self,*args):
        pass

    @vue_method
    async def handle_new_variable(self, *args):
        try:
            var_name = self.new_variable_name
            m = re.match("^[a-zA-Z](?:\\w*[a-zA-Z0-9])?$", var_name)
            if not m:
                js.alert(f"The variable name \"{var_name}\" is invalid")
                return
            
            var_type1 = self.new_variable_type_selected
            if len(var_type1) == 0:
                js.alert(f"The variable type must be selected")
                return
            
            var_type2 = var_type1.split(",")
            var_type = var_type2[0]
            var_tags = var_type2[1:]
            
            db = self.core.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            ex_var_names = await db.async_filter_variables("globals",var_name,[],None)
            if len(ex_var_names) > 0:
                js.alert(f"The variable name \"{var_name}\" already exstis")
                return

            from ..plugins.variable_dialog import show_webui_browser_variable_new_dialog
            show_webui_browser_variable_new_dialog(var_name,var_type,var_tags,self.core)

        except:
            traceback.print_exc()

def register_vue_components():
    vue_register_component("pyri-globals-list", PyriGlobalsListComponent)