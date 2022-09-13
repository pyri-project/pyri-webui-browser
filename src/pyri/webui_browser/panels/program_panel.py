import json
from typing import List, Dict, Callable, Any
import uuid

from ..plugins.panel import PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
import importlib_resources
import js
import traceback
from RobotRaconteur.Client import *
import random
import re
import io
from RobotRaconteurCompanion.Util.UuidUtil import UuidUtil
from ..util import to_js2

async def run_procedure(device_manager, name, vue):
    try:
        c = device_manager.get_device_subscription("sandbox").GetDefaultClient()
        gen = await c.async_execute_procedure(name, [], None)

        res = await gen.AsyncNext(None,None)
        await gen.AsyncClose(None)

        if len(res.printed) > 12:
            res_printed = '\n'.join(res.printed[0:12] + ["..."])
        else:
            res_printed = '\n'.join(res.printed)
        if vue is None:
            js.window.alert(f"Run procedure {name} complete:\n\n{res_printed}")
        else:
            getattr(vue,"$bvToast").toast(f"Run procedure {name} complete:\n\n{res_printed}",
                to_js2({
                    "title": "Run Procedure Complete",
                    "autoHideDelay": 5000,
                    "appendToToast": True,
                    "variant": "success",
                    "toaster": "b-toaster-bottom-center"
                })
            )
        
    except Exception as e:

        msg = f"Run procedure {name} failed:\n\n{traceback.format_exc()}"
        msg1 = msg.splitlines()
        if len(msg1) > 14:
            msg = "\n".join(msg1[0:14] + ["..."])
        if vue is None:
            js.window.alert(msg )
        else:
            getattr(vue,"$bvToast").toast(msg,
                to_js2({
                    "title": "Run Procedure Failed",
                    "autoHideDelay": 5000,
                    "appendToToast": True,
                    "variant": "danger",
                    "toaster": "b-toaster-bottom-center"
                })
            )

async def stop_all_procedure(device_manager):
    try:
        c = device_manager.get_device_subscription("sandbox").GetDefaultClient()
        await c.async_stop_all(None)
       
    except Exception as e:
        
        js.window.alert(f"Stop all procedures failed:\n\n{traceback.format_exc()}" )

async def stop_program_master(device_manager):
    try:
        c = device_manager.get_device_subscription("program_master").GetDefaultClient()
        await c.async_stop(None)
       
    except Exception as e:
        
        js.window.alert(f"Stop program master failed:\n\n{traceback.format_exc()}" )

def do_stop_all(core,device_manager):
    core.create_task(stop_all_procedure(device_manager))
    core.create_task(stop_program_master(device_manager))

def gen_block_uid():

    genUid_soup_ = '!#$%()*+,-./:;=?@[]^_`{|}~ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    length = 20
    soupLength = len(genUid_soup_)
    id_ = []
    for i in range(length):
        id_.append(genUid_soup_[random.randrange(0,soupLength)])
    return ''.join(id_)


def new_blockly_procedure(procedure_name, comment):

    block_id = gen_block_uid()
    new_blockly = {
        "blocks": {
            "languageVersion": 0,
            "blocks": [
            {
                "type": "procedures_defnoreturn",
                "id": block_id,
                "x": 20,
                "y": 20,
                "icons": {
                "comment": {
                    "text": comment,
                    "pinned": False,
                    "height": 80,
                    "width": 160
                }
                },
                "fields": {
                "NAME": procedure_name
                }
            }
            ]
        }
    }
    return new_blockly

class PyriProcedureListPanel(PyriWebUIBrowserPanelBase):

    def __init__(self, core, device_manager):
        self.vue = None
        self.core = core
        self.device_manager = device_manager

    def init_vue(self,vue):
        self.vue = vue    

    def procedure_run(self, name):
        self.core.create_task(run_procedure(self.device_manager,name,self.vue))

    async def do_procedure_open(self,name):
        try:
            var_storage = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            tags = await var_storage.async_getf_variable_tags("procedure",name,None)
            if "pyri" in tags:
                p = PyriEditorProgramPanel(name,self.core,self.device_manager)
            elif "blockly" in tags:
                p = PyriBlocklyProgramPanel(name,self.core,self.device_manager)
            else:
                raise RR.InvalidArgumentException("Procedure is not a Blockly or PyRI procedure!")
        except:
            js.alert(f"Open procedure failed:\n\n{traceback.format_exc()}")

    def procedure_open(self, name):
        self.core.create_task(self.do_procedure_open(name))


    async def do_procedure_copy(self,name,copy_name):
        try:

            var_storage = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
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

    def procedure_copy(self, name):
        copy_name = js.prompt("Procedure copy name")
        self.core.create_task(self.do_procedure_copy(name,copy_name))

    def procedure_info(self, name):
        js.window.alert(f"Procedure info: {name}")

    async def do_procedure_delete(self,name):        
        try:
            var_storage = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            await var_storage.async_delete_variable("procedure", name, None)
        except:
            traceback.print_exc()

    def procedure_delete(self, name):
        if js.window.confirm(f"Delete procedure: {name}?"):
            self.core.create_task(self.do_procedure_delete(name))

    async def do_procedure_selected(self,names):
        try:
            var_storage = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            for name in names:
                await var_storage.async_delete_variable("procedure", name, None)
        except:
            pass

    def procedure_delete_selected(self, *args):
        b_procedure_table = getattr(self.vue,"$refs").procedures_list
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
        
        self.core.create_task(self.do_procedure_delete(names))

    async def do_refresh_procedure_table(self):
        try:
        
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
                getattr(self.vue,"$data").procedures = to_js2(procedures)
        except:
            traceback.print_exc()


    def refresh_procedure_table(self, *args):
        self.core.create_task(self.do_refresh_procedure_table())

    async def do_new_blockly_procedure(self):
        try:
            procedure_name = js.prompt("New procedure name")
            procedure_json = json.dumps(new_blockly_procedure(procedure_name, ""))
            variable_manager = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()

            var_consts = RRN.GetConstants('tech.pyri.variable_storage', variable_manager)
            variable_persistence = var_consts["VariablePersistence"]
            variable_protection_level = var_consts["VariableProtectionLevel"]

            await variable_manager.async_add_variable2("procedure", procedure_name ,"string", \
            RR.VarValue(procedure_json,"string"), ["blockly"], {}, variable_persistence["const"], None, variable_protection_level["read_write"], \
                [], "User defined procedure", False, None)

            p = PyriBlocklyProgramPanel(procedure_name,self.core,self.device_manager)

        except:
            traceback.print_exc()

    def new_blockly_procedure(self, *args):
        self.core.create_task(self.do_new_blockly_procedure())

    async def do_new_pyri_procedure(self):
        try:
            procedure_name = js.prompt("New procedure name")
            pyri_src = f"def {procedure_name}():\n    pass"
            variable_manager = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()

            var_consts = RRN.GetConstants('tech.pyri.variable_storage', variable_manager)
            variable_persistence = var_consts["VariablePersistence"]
            variable_protection_level = var_consts["VariableProtectionLevel"]

            await variable_manager.async_add_variable2("procedure", procedure_name ,"string", \
            RR.VarValue(pyri_src,"string"), ["pyri"], {}, variable_persistence["const"], None, variable_protection_level["read_write"], \
                [], "User defined procedure", False, None)

            p = PyriEditorProgramPanel(procedure_name,self.core,self.device_manager)

        except:
            traceback.print_exc()

    def new_pyri_procedure(self, *args):
        self.core.create_task(self.do_new_pyri_procedure())

    def do_stop_all(self, evt):
        do_stop_all(self.core,self.device_manager)


class PyriGlobalsListPanel(PyriWebUIBrowserPanelBase):

    def __init__(self, core, device_manager):
        self.vue = None
        self.core = core
        self.device_manager = device_manager

    def init_vue(self,vue):
        self.vue = vue    

    def variable_open(self, name):
        js.alert("Variable open")
        #p = PyriBlocklyProgramPanel(name,self.core,self.device_manager)


    async def do_variable_copy(self,name,copy_name):
        try:

            var_storage = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
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

    def variable_copy(self, name):
        copy_name = js.prompt("Variable copy name")
        self.core.create_task(self.do_variable_copy(name,copy_name))

    def variable_info(self, name):
        js.window.alert(f"Variable info: {name}")

    async def do_variable_delete(self,name):        
        try:
            var_storage = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            await var_storage.async_delete_variable("globals", name, None)
        except:
            pass

    def variable_delete(self, name):
        if js.window.confirm(f"Delete global variable: \"{name}\"?"):
            self.core.create_task(self.do_variable_delete(name))

    async def do_variable_delete_selected(self,names):
        try:
            var_storage = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            for name in names:
                await var_storage.async_delete_variable("globals", name, None)
        except:
            pass

    def variable_delete_selected(self, *args):
        
        b_globals_table = getattr(self.vue,"$refs").globals_list
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

        self.core.create_task(self.do_variable_delete_selected(names))

    async def do_refresh_globals_table(self):
        try:
        
            db = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()

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

            if self.vue is not None:
                getattr(self.vue,"$data").variables = to_js2(vars)
        except:
            traceback.print_exc()


    def refresh_globals_table(self, *args):
        self.core.create_task(self.do_refresh_globals_table())
    
    def new_variable(self, *args):
        try:
            self.reset_new_variable()
                        
            getattr(self.vue,"$bvModal").show("new_variable_modal")
        except:
            traceback.print_exc()

    def reset_new_variable(self, *args):
        from ..plugins.variable_dialog import get_all_webui_browser_variable_dialog_infos
        dialog_infos = get_all_webui_browser_variable_dialog_infos()

        select_values=[]
        for d1 in dialog_infos.values():
            for d2 in d1.values():
                v = ",".join([d2.variable_type] + d2.variable_tags)
                select_values.append({"value": v, "text": d2.display_name})

        getattr(self.vue,"$data").new_variable_type_select_options = to_js2(select_values)
        if len(select_values) > 0:
            getattr(self.vue,"$data").new_variable_type_selected = select_values[0]["value"]
        getattr(self.vue,"$data").new_variable_name = ""        

    def handle_new_variable(self, *args):
        self.core.create_task(self.do_handle_new_variable())

    def handle_submit(self,*args):
        pass

    async def do_handle_new_variable(self):
        try:
            var_name = getattr(self.vue,"$data").new_variable_name
            m = re.match("^[a-zA-Z](?:\\w*[a-zA-Z0-9])?$", var_name)
            if not m:
                js.alert(f"The variable name \"{var_name}\" is invalid")
                return
            
            var_type1 = getattr(self.vue,"$data").new_variable_type_selected
            if len(var_type1) == 0:
                js.alert(f"The variable type must be selected")
                return
            
            var_type2 = var_type1.split(",")
            var_type = var_type2[0]
            var_tags = var_type2[1:]
            
            db = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            ex_var_names = await db.async_filter_variables("globals",var_name,[],None)
            if len(ex_var_names) > 0:
                js.alert(f"The variable name \"{var_name}\" already exstis")
                return

            from ..plugins.variable_dialog import show_webui_browser_variable_new_dialog
            show_webui_browser_variable_new_dialog(var_name,var_type,var_tags,self.core)

        except:
            traceback.print_exc()

class PyriOutputPanel:
    def __init__(self, core, device_manager):
        self.core = core
        self.device_manager = device_manager

    async def run(self):
        try:
            while True:
                try:
                    sandbox = self.device_manager.get_device_subscription("sandbox").GetDefaultClient()
                    output_type_consts = RRN.GetConstants("tech.pyri.sandbox",sandbox)["ProcedureOutputTypeCode"]
                except Exception:
                    traceback.print_exc()
                    await RRN.AsyncSleep(2, None)
                    continue
                try:
                    gen = await sandbox.async_getf_output(None)
                    try:
                        while True:
                            output_list = await gen.AsyncNext(None,None)
                            output_el = js.document.getElementById("procedure_output_inner_div")
                            anchor_el = js.document.getElementById("procedure_output_div_anchor")
                            for l in output_list.output_list:
                                span = js.document.createElement('div')
                                span.innerText = l.output
                                span.style = "white-space: pre-line"
                                css_classes = ["text-monospace", "d-block"]
                                if l.output_type == output_type_consts["status"]:
                                    css_classes.append("text-success")
                                elif l.output_type == output_type_consts["info"]:
                                    css_classes.append("text-info")
                                elif l.output_type == output_type_consts["error"]:
                                    css_classes.append("text-danger")
                                elif l.output_type == output_type_consts["debug"]:
                                    css_classes.append("text-muted")
                                span.className = " ".join(css_classes)
                                # https://blog.eqrion.net/pin-to-bottom/                       
                                output_el.insertBefore(span,anchor_el)
                    except RR.StopIterationException:
                            continue
                except Exception:
                    traceback.print_exc()
                    await RRN.AsyncSleep(0.5, None)
                    continue
                
        except:
            traceback.print_exc()

async def add_program_panel(panel_type: str, core: PyriWebUIBrowser, parent_element: Any):

    assert panel_type == "program"


    program_panel_config = {
        "type": "stack",
        "componentName": "program",
        "componentState": {},
        "title": "Program",
        "id": "program",
        "isClosable": False
    }

    core.layout.register_component("program",False)

    core.layout.add_panel(program_panel_config)

    core.layout.add_panel_menu_item("program", "Program")


    program_main_panel_html = importlib_resources.read_text(__package__,"program_main_panel.html")

    def register_program_main_panel(container, state):
        container.getElement().html(program_main_panel_html)

    core.layout.register_component(f"program_main",register_program_main_panel)

    program_main_panel=PyriProgramMainPanel(core,core.device_manager)

    core.create_task(program_main_panel.run())

    procedure_list_panel_html = importlib_resources.read_text(__package__,"program_panel.html")

    procedure_list_panel_config = {
        "type": "component",
        "componentName": "procedure_list",
        "componentState": {},
        "title": "Procedure List",
        "id": "procedure_list",
        "isClosable": False
    }

    gl = core.layout.layout

    def register_procedure_list_panel(container, state):
        container.getElement().html(procedure_list_panel_html)

    core.layout.register_component("procedure_list",register_procedure_list_panel)

    core.layout.layout.root.getItemsById("program")[0].addChild(to_js2(procedure_list_panel_config))

    procedure_list_panel_obj = PyriProcedureListPanel(core, core.device_manager)

    program_panel = js.Vue.new(to_js2({
        "el": "#procedures_table",
        "components": {
            "BootstrapTable": js.window.BootstrapTable
        },
        "data":
        {
            "procedures": [],
            "procedures_columns": [
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
                        "click .procedure_list_play": lambda e, value, row, d: procedure_list_panel_obj.procedure_run(row.procedure_name),
                        "click .procedure_list_open": lambda e, value, row, d: procedure_list_panel_obj.procedure_open(row.procedure_name),
                        "click .procedure_list_copy": lambda e, value, row, d: procedure_list_panel_obj.procedure_copy(row.procedure_name),
                        "click .procedure_list_info": lambda e, value, row, d: procedure_list_panel_obj.procedure_info(row.procedure_name),
                        "click .procedure_list_remove": lambda e, value, row, d: procedure_list_panel_obj.procedure_delete(row.procedure_name)
                    }
                }
            ],
            "procedures_list_options":
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
        },
        "methods":
        {
            "procedure_run": procedure_list_panel_obj.procedure_run,
            "procedure_open": procedure_list_panel_obj.procedure_open,
            "procedure_copy": procedure_list_panel_obj.procedure_copy,
            "procedure_info": procedure_list_panel_obj.procedure_info,
            "procedure_delete": procedure_list_panel_obj.procedure_delete,
            "procedure_delete_selected": procedure_list_panel_obj.procedure_delete_selected,
            "refresh_procedure_table": procedure_list_panel_obj.refresh_procedure_table,
            "new_blockly_procedure": procedure_list_panel_obj.new_blockly_procedure,
            "new_pyri_procedure": procedure_list_panel_obj.new_pyri_procedure,
            "stop_all": procedure_list_panel_obj.do_stop_all,
        }
    }))

    procedure_list_panel_obj.init_vue(program_panel)

    blockly_panel_html = importlib_resources.read_text(__package__,"procedure_blockly_panel.html")

    def register_blockly_panel(container, state):
        container.getElement().html(blockly_panel_html)

    core.layout.register_component(f"procedure_blockly",register_blockly_panel)

    pyri_panel_html = importlib_resources.read_text(__package__,"procedure_pyri_panel.html")

    def register_pyri_panel(container, state):
        container.getElement().html(pyri_panel_html)

    core.layout.register_component(f"procedure_pyri",register_pyri_panel)

    add_globals_panel(core)

    add_output_panel(core)

    p = core.layout.layout.root.getItemsById("program")[0].getItemsById("program_main_main")
    p[0].parent.setActiveContentItem(p[0])
    
    return procedure_list_panel_obj

def add_globals_panel(core):
    globals_list_panel_html = importlib_resources.read_text(__package__,"globals_panel.html")

    globals_list_panel_config = {
        "type": "component",
        "componentName": "globals_list",
        "componentState": {},
        "title": "Globals List",
        "id": "globals_list",
        "isClosable": False
    }

    gl = core.layout.layout

    def register_globals_list_panel(container, state):
        container.getElement().html(globals_list_panel_html)

    core.layout.register_component("globals_list",register_globals_list_panel)

    core.layout.layout.root.getItemsById("program")[0].addChild(to_js2(globals_list_panel_config))

    globals_list_panel_obj = PyriGlobalsListPanel(core, core.device_manager)

    globals_panel = js.Vue.new(to_js2({
        "el": "#globals_table",
        "components": {
            "BootstrapTable": js.window.BootstrapTable
        },
        "data":
        {
            "variables": [],
            "variables_columns":
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
                        "click .globals_table_open": lambda e, value, row, d: globals_list_panel_obj.variable_open(row.variable_name),
                        "click .globals_table_copy": lambda e, value, row, d: globals_list_panel_obj.variable_copy(row.variable_name),
                        "click .globals_table_info": lambda e, value, row, d: globals_list_panel_obj.variable_info(row.variable_name),
                        "click .globals_table_remove": lambda e, value, row, d: globals_list_panel_obj.variable_delete(row.variable_name),
                    }
                }
            ],
            "new_variable_type_selectedState": "",
            "new_variable_type_selected": "",
            "new_variable_name_inputState": "",
            "new_variable_name": "",
            "new_variable_type_select_options": [],
            "variables_options":
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
        },
        "methods":
        {            
            "variable_open": globals_list_panel_obj.variable_open,
            "variable_copy": globals_list_panel_obj.variable_copy,
            "variable_info": globals_list_panel_obj.variable_info,
            "variable_delete": globals_list_panel_obj.variable_delete,
            "variable_delete_selected": globals_list_panel_obj.variable_delete_selected,
            "refresh_globals_table": globals_list_panel_obj.refresh_globals_table,
            "new_variable": globals_list_panel_obj.new_variable,
            "reset_new_variable": globals_list_panel_obj.reset_new_variable,
            "handle_new_variable": globals_list_panel_obj.handle_new_variable,
            "handle_submit": globals_list_panel_obj.handle_submit

        }
    }))

    globals_list_panel_obj.init_vue(globals_panel)

def add_output_panel(core):
    output_panel_html = importlib_resources.read_text(__package__,"output_panel.html")

    output_list_panel_config = {
        "type": "component",
        "componentName": "procedure_output",
        "componentState": {},
        "title": "Output",
        "id": "procedure_output_panel",
        "isClosable": False
    }

    def register_output_panel(container, state):
        container.getElement().html(output_panel_html)

    core.layout.register_component("procedure_output",register_output_panel)

    core.layout.layout.root.getItemsById("program")[0].addChild(to_js2(output_list_panel_config))

    output_panel_obj = PyriOutputPanel(core, core.device_manager)
    core.create_task(output_panel_obj.run())

class PyriBlocklyProgramPanel(PyriWebUIBrowserPanelBase):
    def __init__(self, procedure_name: str, core: PyriWebUIBrowser, device_manager):
        self.vue = None
        self.core = core
        self.device_manager = device_manager
        self.procedure_name = procedure_name
        
        blockly_panel_config = {
            "type": "component",
            "componentName": f"procedure_blockly",
            "componentState": {
                "procedure_name": procedure_name
            },
            "title": procedure_name,
            "id": f"procedure_blockly_{procedure_name}",
            "isClosable": True
        }
       
        core.layout.layout.root.getItemsById("program")[0].addChild(to_js2(blockly_panel_config))
        res = core.layout.layout.root.getItemsById(f"procedure_blockly_{procedure_name}")[0].element.find("#procedure_blockly_component")[0]
                
        procedure_panel = js.Vue.new(to_js2({
            "el": res,
            "data":
            {
                "procedure_name": procedure_name
            },
            "methods":
            {
                "save": self.do_save,
                "run": self.do_run,
                "iframe_load": self.iframe_loaded,
                "stop_all": self.do_stop_all,
            }
        }))

        self.vue = procedure_panel    

    def iframe_loaded(self, evt):

        self.core.create_task(self.do_iframe_loaded())

    async def do_iframe_loaded(self):
        try:
            
            variable_manager = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()

            procedure_src = await variable_manager.async_getf_variable_value("procedure",self.procedure_name,None)

            iframe = self.core.layout.layout.root.getItemsById(f"procedure_blockly_{self.procedure_name}")[0]\
                .element.find("#procedure_blockly_iframe")[0].contentWindow

            delay_count = 0
            while not iframe.blocklyReady():
                delay_count+=1
                assert delay_count < 100
                await RRN.AsyncSleep(0.1,None)

            iframe.setBlocklyJsonText(procedure_src.data)
        except:
            traceback.print_exc()

    def do_save(self, evt):
        iframe = self.core.layout.layout.root.getItemsById(f"procedure_blockly_{self.procedure_name}")[0]\
                .element.find("#procedure_blockly_iframe")[0].contentWindow

        blockly_json = iframe.getBlocklyJsonText()

        async def s():
            try:
                variable_manager = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
                await variable_manager.async_setf_variable_value("procedure",self.procedure_name,RR.VarValue(blockly_json,"string"),None)
            except:
                traceback.print_exc()
        
        self.core.create_task(s())

        

    def do_run(self, evt):
        self.core.create_task(run_procedure(self.device_manager,self.procedure_name,self.vue))

    def do_stop_all(self, evt):
        do_stop_all(self.core,self.device_manager)


class PyriEditorProgramPanel(PyriWebUIBrowserPanelBase):
    def __init__(self, procedure_name: str, core: PyriWebUIBrowser, device_manager):
        self.vue = None
        self.core = core
        self.device_manager = device_manager
        self.procedure_name = procedure_name
        
        pyri_panel_config = {
            "type": "component",
            "componentName": f"procedure_pyri",
            "componentState": {
                "procedure_name": procedure_name
            },
            "title": procedure_name,
            "id": f"procedure_pyri_{procedure_name}",
            "isClosable": True
        }
       
        core.layout.layout.root.getItemsById("program")[0].addChild(to_js2(pyri_panel_config))
        res = core.layout.layout.root.getItemsById(f"procedure_pyri_{procedure_name}")[0].element.find("#procedure_pyri_component")[0]
                
        procedure_panel = js.Vue.new(to_js2({
            "el": res,
            "data":
            {
                "procedure_name": procedure_name,
                "insert_function_selected": None,
                "insert_function_options": [],
                "insert_function_selected_doc": ""
            },
            "methods":
            {
                "save": self.do_save,
                "run": self.do_run,
                "iframe_load": self.iframe_loaded,
                "stop_all": self.do_stop_all,
                "cursor_left": self.cursor_left,
                "cursor_right": self.cursor_right,
                "cursor_up": self.cursor_up,
                "cursor_down": self.cursor_down,
                "cursor_home": self.cursor_home,
                "cursor_end": self.cursor_end,
                "cursor_outdent": self.cursor_outdent,
                "cursor_indent": self.cursor_indent,
                "move_line_down": self.move_line_down,
                "move_line_up": self.move_line_up,
                "editor_newline": self.editor_newline,
                "editor_select_more": self.editor_select_more,
                "editor_select_less": self.editor_select_less,
                "editor_delete_left": self.editor_delete_left,
                "editor_delete_right": self.editor_delete_right,
                "editor_delete_line": self.editor_delete_line,
                "editor_comment_line": self.editor_comment_line,
                "editor_remove_comment_line": self.editor_remove_comment_line,
                "editor_find": self.editor_find,
                "editor_replace": self.editor_replace,
                "editor_gotoline": self.editor_gotoline,
                "editor_undo": self.editor_undo,
                "editor_redo": self.editor_redo,
                "insert_function": self.insert_function,
                "insert_function_selected_changed": self.insert_function_selected_changed,
                "insert_function_ok": self.insert_function_ok,
                "insert_function_hidden": self.insert_function_hidden
            }
        }))

        self.vue = procedure_panel    

    def iframe_loaded(self, evt):

        self.core.create_task(self.do_iframe_loaded())

    async def do_iframe_loaded(self):
        try:
            
            variable_manager = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()

            procedure_src = await variable_manager.async_getf_variable_value("procedure",self.procedure_name,None)

            iframe = self.core.layout.layout.root.getItemsById(f"procedure_pyri_{self.procedure_name}")[0]\
                .element.find("#procedure_pyri_iframe")[0].contentWindow

            delay_count = 0
            while not iframe.editorReady():
                delay_count+=1
                assert delay_count < 100
                await RRN.AsyncSleep(0.1,None)

            iframe.setValue(procedure_src.data)
        except:
            traceback.print_exc()

    def do_save(self, evt):
        iframe = self.core.layout.layout.root.getItemsById(f"procedure_pyri_{self.procedure_name}")[0]\
                .element.find("#procedure_pyri_iframe")[0].contentWindow

        pyri_src = iframe.getValue()

        async def s():
            try:
                variable_manager = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
                await variable_manager.async_setf_variable_value("procedure",self.procedure_name,RR.VarValue(pyri_src,"string"),None)
            except:
                traceback.print_exc()
        
        self.core.create_task(s())

        

    def do_run(self, evt):
        self.core.create_task(run_procedure(self.device_manager,self.procedure_name,self.vue))

    def do_stop_all(self, evt):
        do_stop_all(self.core,self.device_manager)

    def _get_iframe(self):
        iframe = self.core.layout.layout.root.getItemsById(f"procedure_pyri_{self.procedure_name}")[0]\
                .element.find("#procedure_pyri_iframe")[0].contentWindow
        return iframe

    def cursor_left(self,evt):
        self._get_iframe().cursorLeft()

    def cursor_right(self,evt):
        self._get_iframe().cursorRight()

    def cursor_up(self,evt):
        self._get_iframe().cursorUp()

    def cursor_down(self,evt):
        self._get_iframe().cursorDown()

    def cursor_home(self,evt):
        self._get_iframe().home()

    def cursor_end(self,evt):
        self._get_iframe().end()

    def cursor_outdent(self,evt):
        self._get_iframe().outdentLines()

    def cursor_indent(self,evt):
        self._get_iframe().indentLines()

    def move_line_up(self,evt):
        self._get_iframe().moveLineUp()

    def move_line_down(self,evt):
        self._get_iframe().moveLineDown()

    def editor_newline(self,evt):
        self._get_iframe().newline()

    def editor_select_more(self,evt):
        self._get_iframe().selectMore()
    
    def editor_select_less(self,evt):
        self._get_iframe().selectLess()

    def editor_delete_left(self,evt):
        self._get_iframe().deleteLeft()

    def editor_delete_right(self,evt):
        self._get_iframe().deleteRight()

    def editor_delete_line(self,evt):
        self._get_iframe().deleteLine()

    def editor_find(self,evt):
        self._get_iframe().find()

    def editor_replace(self,evt):
        self._get_iframe().replace()
    
    def editor_gotoline(self,evt):
        self._get_iframe().gotoline()

    def editor_undo(self,evt):
        self._get_iframe().undo()

    def editor_redo(self,evt):
        self._get_iframe().redo()

    def editor_comment_line(self,evt):
        self._get_iframe().commentLine()

    def editor_remove_comment_line(self,evt):
        self._get_iframe().removeCommentLine()

    async def do_insert_function(self):
        try:
            res = await js.fetch('/sandbox_functions/all_functions.json', {"cache": "no-store"})
            res_io = io.TextIOWrapper(io.BytesIO((await res.arrayBuffer()).to_py()),encoding="utf-8")
            res_str = res_io.read()

            res_json = json.loads(res_str)

            all_functions_list = res_json["all_functions"]
            all_functions = {}
            for v in all_functions_list:
                all_functions[v["name"]] = v

            self.all_functions = all_functions

            opts = []
            for v in self.all_functions.values():
                opts.append({
                    "value": v["name"],
                    "text": v["full_signature"]
                })

            getattr(self.vue,"$data").insert_function_options = to_js2(opts)

            getattr(self.vue,"$bvModal").show("insert-function-modal")
        except:
            traceback.print_exc()

    def insert_function(self,evt):
        self.core.create_task(self.do_insert_function())

    def insert_function_selected_changed(self,value):
        if value is None:
            return

        try:
            v = self.all_functions[value]
            getattr(self.vue,"$data").insert_function_selected_doc = v["docstring"] or ""
        except:
            traceback.print_exc()

    def insert_function_ok(self,evt):
        try:
            value = getattr(self.vue,"$data").insert_function_selected
            if value is None:
                return
            v = self.all_functions[value]

            iframe = self._get_iframe()
            iframe.insertText(v["full_signature"])

        except:
            traceback.print_exc()

    def insert_function_hidden(self,*args):
        getattr(self.vue,"$data").insert_function_selected_doc = ""
        getattr(self.vue,"$data").insert_function_selected = None

class PyriProgramMainPanel(PyriWebUIBrowserPanelBase):
    def __init__(self, core: PyriWebUIBrowser, device_manager):

        self.vue = None
        self.core = core
        self.device_manager = device_manager
        self.program_name = "main"
        self.current_program = None
        
        main_panel_config = {
            "type": "component",
            "componentName": f"program_main",
            "componentState": {
                "program_name": "main"
            },
            "title": "Main",
            "id": f"program_main_main",
            "isClosable": False
        }

        core.layout.layout.root.getItemsById("program")[0].addChild(to_js2(main_panel_config))
        res = core.layout.layout.root.getItemsById(f"program_main_main")[0].element.find("#program_main_panel")[0]

        program_main_panel = js.Vue.new(to_js2({
            "el": res,
            "data":
            {
                "program_name": "main",
                "program_steps": [],
                "edit_step_name": "",
                "edit_step_uuid": None,
                "edit_step_index": -1,
                "edit_step_procedure_name": "",
                "edit_step_procedure_args": "",
                "edit_step_next_steps": ""
            },
            "methods":
            {
                "save": self.save,
                "reload": self.reload,
                "run": self.run_btn,
                "step_one": self.step_one,
                "pause": self.pause,
                "stop_all": self.stop_all,
                "add_step": self.add_step,
                "move_cursor_to_step": self.move_cursor_to_step,
                "move_step_up": self.move_step_up,
                "move_step_down": self.move_step_down,
                "delete_step": self.delete_step,
                "configure_step": self.configure_step,
                "clear_error": self.clear_error,
                "clear_pointer": self.clear_pointer,
                "edit_step_ok": self.edit_step_ok
            }
        }))

        self.vue = program_main_panel

        self.highlighted_step_uuid = None
        self.highlighted_step_class = None

        self.core.create_task(self.do_reload())
         
    def _get_client(self):
        return self.device_manager.get_device_subscription("program_master").GetDefaultClient()

    async def do_save(self):
        try:
            program = self.current_program
            assert program is not None, "Internal program error"
            program_var = RR.VarValue(program,"tech.pyri.program_master.PyriProgram")
            var_storage = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            exists_l = await var_storage.async_filter_variables("program", "main", [], None)
            if len(exists_l) > 0:
                await var_storage.async_setf_variable_value("program",self.program_name,program_var,None)
            else:
                var_consts = RRN.GetConstants('tech.pyri.variable_storage', var_storage)
                variable_persistence = var_consts["VariablePersistence"]
                variable_protection_level = var_consts["VariableProtectionLevel"]
                var_storage.async_add_variable2("program","main","tech.pyri.program_master.PyriProgram", \
                    RR.VarValue(program,"tech.pyri.program_master.PyriProgram"), ["program"], {}, variable_persistence["const"], \
                    None, variable_protection_level["read_write"], \
                    [], "test state machine program", False, None)
        except:
            js.alert(f"Run failed :\n\n{traceback.format_exc()}")

    def save(self, evt):
        self.core.create_task(self.do_save())

    def _op_code_to_class(self,opcode):
        if opcode == 1:
            return "program_main_step_op_stop"
        elif opcode == 2:
            return "program_main_step_op_next"
        elif opcode == 3:
            return "program_main_step_op_jump"
        elif opcode == 4:
            return "program_main_step_op_error"
        
        return "program_main_step_op_error"

    def _program_to_plain(self,program):
        uuid_util = UuidUtil(client_obj=self._get_client())
        ret = []
        for s1 in program.steps:
            uuid_str = uuid_util.UuidToString(s1.step_id)
            s2 = dict()
            s2["name"] = s1.step_name
            s2["procedure"] = s1.procedure_name
            s2["procedure_args"] = ", ".join(s1.procedure_args)
            s2["card_id"] = f"program-main-step_{uuid_str}"
            next_steps = []
            for n in s1.next:
                jump_target = ""
                if n.op_code == 3:
                    jump_target_uuid = uuid_util.UuidToPyUuid(n.jump_target)
                    for s3 in program.steps:
                        if uuid_util.UuidToPyUuid(s3.step_id) == jump_target_uuid:
                            jump_target = s3.step_name
                            break

                next_steps.append(
                    {
                        "result": n.result,
                        "op_code_class": self._op_code_to_class(n.op_code),
                        "jump_target": jump_target
                    }
                )
                s2["next_steps"] = next_steps

            ret.append(s2)
        return ret

    async def do_reload(self, show_error = False):
        try:
            var_storage = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
            program = await var_storage.async_getf_variable_value("program",self.program_name,None)
            getattr(self.vue,"$data").program_steps = to_js2(self._program_to_plain(program.data))
            self.current_program = program.data
        except:
            if show_error:
                js.alert(f"Program main load failed:\n\n{traceback.format_exc()}")
            else:
                traceback.print_exc()

    def reload(self, evt):
        self.core.create_task(self.do_reload(True))

    async def do_run(self):
        try:
            await self._get_client().async_run(None)
        except:
            js.alert(f"Run failed :\n\n{traceback.format_exc()}")

    def run_btn(self, evt):
        self.core.create_task(self.do_run())

    async def do_step_one(self):
        try:
            await self._get_client().async_step_one(None)
        except:
            js.alert(f"Step one failed :\n\n{traceback.format_exc()}")

    def step_one(self, evt):
        self.core.create_task(self.do_step_one())

    async def do_pause(self):
        try:
            await self._get_client().async_pause(None)
        except:
            js.alert(f"Pause failed :\n\n{traceback.format_exc()}")

    def pause(self, evt):
        self.core.create_task(self.do_pause())

    def stop_all(self, evt):
        do_stop_all(self.core,self.device_manager)

    def add_step(self, evt):
        try:
            self.fill_edit_step(-1)
            getattr(self.vue,"$bvModal").show("program_main_edit_step_modal")
        except:
            traceback.print_exc()

    async def do_move_cursor_to_step(self,step_id):
        try:
            await self._get_client().async_setf_step_pointer(step_id,None)
        except:
            js.alert(f"Move cursor to step failed :\n\n{traceback.format_exc()}")


    async def do_clear_error(self):
        try:
            await self._get_client().async_clear_errors(None)
        except:
            js.alert(f"Clear errors failed :\n\n{traceback.format_exc()}")

    def clear_error(self,evt):
        self.core.create_task(self.do_clear_error())

    async def do_clear_pointer(self):
        try:
            await self._get_client().async_clear_step_pointer(None)
        except:
            js.alert(f"Clear step pointer failed :\n\n{traceback.format_exc()}")

    def clear_pointer(self,evt):
        self.core.create_task(self.do_clear_pointer())
        

    def move_cursor_to_step(self, index):
        try:
            step_id = self.current_program.steps[index].step_id
            self.core.create_task(self.do_move_cursor_to_step(step_id))
        except:
            js.alert(f"Move cursor to step failed :\n\n{traceback.format_exc()}")

    def move_step_up(self, index):
        try:
            program = self.current_program
            if index == 0:
                return

            step = program.steps.pop(index)
            program.steps.insert(index-1,step)
            
            getattr(self.vue,"$data").program_steps = to_js2(self._program_to_plain(program))
            self.current_program = program
            self.highlighted_step_class = None
            self.highlighted_step_uuid = None
        except:
            js.alert(f"Move step up failed :\n\n{traceback.format_exc()}")

    def move_step_down(self, index):
        try:
            program = self.current_program
            if not index < len(program.steps)-1:
                return
            step = program.steps.pop(index)
            program.steps.insert(index+1,step)
            
            getattr(self.vue,"$data").program_steps = to_js2(self._program_to_plain(program))
            self.current_program = program
            self.highlighted_step_class = None
            self.highlighted_step_uuid = None
        except:
            js.alert(f"Move step down failed :\n\n{traceback.format_exc()}")


    def delete_step(self, index):
        try:
            program = self.current_program
            program.steps.pop(index)
            
            getattr(self.vue,"$data").program_steps = to_js2(self._program_to_plain(program))
            self.current_program = program
            self.highlighted_step_class = None
            self.highlighted_step_uuid = None
        except:
            js.alert(f"Move step down failed :\n\n{traceback.format_exc()}")

    def configure_step(self, index):
        try:
            self.fill_edit_step(index)
            getattr(self.vue,"$bvModal").show("program_main_edit_step_modal")
        except:
            traceback.print_exc()

    def _get_card_header(self,card_id):

        if card_id == f"program-main-step_00000000-0000-0000-0000-000000000000":
            return js.document.getElementById("program_main_start_marker")

        el = js.document.getElementById(card_id)
        if el is None:
            return None
        els2 = el.getElementsByClassName("card-header")
        if len(els2) > 0:
            return els2[0]
        else:
            return None        

    async def run(self):
        await RRN.AsyncSleep(0.1,None)
        
        self.highlighted_step_uuid = None
        self.highlighted_step_class = None

        while True:
            try:
                try:
                    program_master_state = None
                    if self.core.devices_states is not None:
                        e_state = self.core.devices_states.devices_states["program_master"].state
                        if e_state is not None:
                            for e in e_state:
                                if e.type == "tech.pyri.program_master.PyriProgramState":
                                    program_master_state = e.state_data.data
                except KeyError:
                    traceback.print_exc()
                else:
                    if program_master_state is not None:
                        current_step_uuid = _rr_uuid_to_py_uuid(program_master_state.current_step)
                        flags = program_master_state.program_state_flags
                        if (flags & 0x2) != 0:
                            step_class = "bg-danger"
                        elif (flags & 0x10) != 0:
                            step_class = "bg-warning"
                        elif (flags & 0x8) != 0:
                            step_class = "bg-success"
                        else:
                            step_class = "bg-info"
                        if self.highlighted_step_uuid != current_step_uuid:
                            if self.highlighted_step_uuid is not None:
                                highlighted_el = self._get_card_header(f"program-main-step_{str(self.highlighted_step_uuid)}")
                                if highlighted_el is not None:
                                    highlighted_el.className = "card-header"
                                self.highlighted_step_uuid = None
                                self.highlighted_step_class = None
                            
                        
                            highlighted_el = self._get_card_header(f"program-main-step_{str(current_step_uuid)}")
                            if highlighted_el is not None:
                                highlighted_el.className = f"card-header {step_class}"
                                self.highlighted_step_uuid = current_step_uuid
                                self.highlighted_step_class = step_class

                        if self.highlighted_step_uuid is not None and self.highlighted_step_class != step_class:
                            highlighted_el = self._get_card_header(f"program-main-step_{str(self.highlighted_step_uuid)}")
                            if highlighted_el is not None:
                                highlighted_el.className = f"card-header {step_class}"
                                self.highlighted_step_class = step_class

            except:
                traceback.print_exc()

            await RRN.AsyncSleep(0.2,None)

    def edit_step_ok(self, evt):
        name_regex = "^[a-zA-Z](?:\\w*[a-zA-Z0-9])?$"
        step_regex = r"^(\w+)\s+(?:(stop)|(next)|(error)|(?:(jump))\s+([a-zA-Z](?:\w*[a-zA-Z0-9])?))$"
        try:
            step_name = getattr(self.vue,"$data").edit_step_name.strip()
            m = re.match(name_regex, step_name)
            if m is None:
                js.alert(f"Invalid step name: {step_name}")
                evt.preventDefault()
                return

            procedure_name = getattr(self.vue,"$data").edit_step_procedure_name.strip()
            m = re.match(name_regex, procedure_name)
            if m is None:
                js.alert(f"Invalid procedure name: {procedure_name}")
                evt.preventDefault()
                return

            procedure_args = getattr(self.vue,"$data").edit_step_procedure_args.strip().splitlines()
            procedure_args = [s.strip() for s in procedure_args]
            if "" in procedure_args:
                js.alert(f"Invalid procedure args: {', '.join(procedure_args)}")
                evt.preventDefault()
                return

            next_steps = getattr(self.vue,"$data").edit_step_next_steps.strip().splitlines()
            for p in next_steps:
                m = re.match(step_regex, p)
                if m is None:
                    js.alert(f"Invalid next steps: {', '.join(next_steps)}")
                    evt.preventDefault()
                    return
                if m.group(5) is not None:
                    jump_target_name = m.group(6)
                    jump_target_found = False
                    for s1 in self.current_program.steps:
                        if s1.step_name == jump_target_name:
                            jump_target_found = True
                    if not jump_target_found:
                        js.alert(f"Invalid jump target: {jump_target_name}")
                        evt.preventDefault()
                        return

            step_index = getattr(self.vue,"$data").edit_step_index
            step_uuid = uuid.UUID(getattr(self.vue,"$data").edit_step_uuid)

            client = self._get_client()
            uuid_util = UuidUtil(client_obj = client)

            if step_index < 0:
                step = RRN.NewStructure("tech.pyri.program_master.PyriProgramStep", client)
                step.step_id = uuid_util.UuidFromPyUuid(step_uuid)
            else:
                step = self.current_program.steps[step_index]
                assert step_uuid == _rr_uuid_to_py_uuid(step.step_id), "Internal error updating step"

            step.step_name = step_name
            step.procedure_name = procedure_name
            step.procedure_args = procedure_args

            next_steps2 = []
            for p in next_steps:
                n = RRN.NewStructure("tech.pyri.program_master.PyriProgramStepNext", client)
                m = re.match(step_regex, p)
                n.result = m.group(1)
                n.jump_target = uuid_util.UuidFromPyUuid(uuid.UUID(bytes=b'\x00'*16))
                if m.group(2) is not None:
                    n.op_code = 1
                elif m.group(3) is not None:
                    n.op_code = 2
                elif m.group(4) is not None:
                    n.op_code = 4
                elif m.group(5) is not None:
                    n.op_code = 3
                    jump_target_name = m.group(6)
                    jump_target_uuid = None
                    if self.current_program is not None:
                        for s1 in self.current_program.steps:
                            if s1.step_name == jump_target_name:
                                jump_target_uuid = s1.step_id
                    assert jump_target_uuid is not None, f"Internal error finding jump target {jump_target_name}"
                    n.jump_target = jump_target_uuid

                next_steps2.append(n)

            step.next = next_steps2

            if step_index < 0:
                if self.current_program is None:
                    self.current_program = RRN.NewStructure("tech.pyri.program_master.PyriProgram", client)
                    self.current_program.steps=[]
                    self.current_program.name="main"
                self.current_program.steps.append(step)
            
            getattr(self.vue,"$data").program_steps = to_js2(self._program_to_plain(self.current_program))
            self.highlighted_step_class = None
            self.highlighted_step_uuid = None

        except:
            js.alert(f"Error applying changes:\n\n{traceback.format_exc()}")

    def fill_edit_step(self, index):
        step = None
        if index >= 0:
            try:
                step = self.current_program.steps[index]
            except IndexError:
                pass
        if step is not None:
            getattr(self.vue,"$data").edit_step_name = step.step_name
            getattr(self.vue,"$data").edit_step_uuid = str(_rr_uuid_to_py_uuid(step.step_id))
            getattr(self.vue,"$data").edit_step_index = index
            getattr(self.vue,"$data").edit_step_procedure_name = step.procedure_name
            getattr(self.vue,"$data").edit_step_procedure_args = "\n".join(step.procedure_args)
            next_steps = []
            for n in step.next:
                if n.op_code == 1:
                    next_steps.append(f"{n.result} stop")
                elif n.op_code == 2:
                    next_steps.append(f"{n.result} next")
                elif n.op_code == 3:
                    jump_target = None
                    jump_target_uuid = _rr_uuid_to_py_uuid(n.jump_target)
                    for s3 in self.current_program.steps:
                        if _rr_uuid_to_py_uuid(s3.step_id) == jump_target_uuid:
                            jump_target = s3.step_name
                            break
                    if jump_target is None:
                        next_steps.append(f"{n.result} error")    
                    else:
                        next_steps.append(f"{n.result} jump {str(jump_target)}")
                elif n.op_code == 4:
                    next_steps.append(f"{n.result} error")
                else:
                    next_steps.append(f"{n.result} error")
            
            getattr(self.vue,"$data").edit_step_next_steps = "\n".join(next_steps)
        else:
            new_ind = 0
            if self.current_program is not None:
                new_ind = len(self.current_program.steps)
                for s in self.current_program.steps:
                    m = re.match(r"^step(\d+)$", s.step_name)
                    if m is not None:
                        ind1 = int(m.group(1))
                        if ind1 > new_ind:
                            new_ind = ind1

            getattr(self.vue,"$data").edit_step_name = f"step{new_ind+1}"
            getattr(self.vue,"$data").edit_step_uuid = str(uuid.uuid4())
            getattr(self.vue,"$data").edit_step_index = -1
            getattr(self.vue,"$data").edit_step_procedure_name = "my_procedure"
            getattr(self.vue,"$data").edit_step_procedure_args = ""
            getattr(self.vue,"$data").edit_step_next_steps = "DEFAULT next\nERROR error"

def _rr_uuid_to_py_uuid(rr_uuid):
    uuid_bytes = rr_uuid["uuid_bytes"].tobytes()
    return uuid.UUID(bytes=uuid_bytes)