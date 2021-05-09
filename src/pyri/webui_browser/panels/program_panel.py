import json
from typing import List, Dict, Callable, Any
from ..plugins.panel import PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
import importlib_resources
import js
import traceback
from RobotRaconteur.Client import *
import random
import re
import io

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
            vue["$bvToast"].toast(f"Run procedure {name} complete:\n\n{res_printed}",
                js.python_to_js({
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
            vue["$bvToast"].toast(msg,
                js.python_to_js({
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
    new_blockly= """<xml xmlns="https://developers.google.com/blockly/xml">
    <block type="procedures_defnoreturn" id=\"""" + block_id + """\" x="20" y="20" deletable="false" movable="false" editable="true">
      <field name="NAME">""" + procedure_name + """</field>
      <comment pinned="false" h="80" w="160">""" + comment + """</comment>
      <statement name="STACK"></statement></block></xml>"""
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
            pass

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
        b_procedure_table = self.vue["$refs"].procedures_list
        selections = b_procedure_table.getSelections()
        names = []
        count = len(selections)
        for i in range(count):
            t = selections[i]
            names.append(t["procedure_name"])

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
                self.vue["$data"].procedures = js.python_to_js(procedures)
        except:
            traceback.print_exc()


    def refresh_procedure_table(self, *args):
        self.core.create_task(self.do_refresh_procedure_table())

    async def do_new_blockly_procedure(self):
        try:
            procedure_name = js.prompt("New procedure name")
            procedure_xml = new_blockly_procedure(procedure_name, "")
            variable_manager = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()

            var_consts = RRN.GetConstants('tech.pyri.variable_storage', variable_manager)
            variable_persistence = var_consts["VariablePersistence"]
            variable_protection_level = var_consts["VariableProtectionLevel"]

            await variable_manager.async_add_variable2("procedure", procedure_name ,"string", \
            RR.VarValue(procedure_xml,"string"), ["blockly"], {}, variable_persistence["const"], None, variable_protection_level["read_write"], \
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
        
        b_globals_table = self.vue["$refs"].globals_list
        selections = b_globals_table.getSelections()
        names = []
        count = len(selections)
        for i in range(count):
            t = selections[i]
            names.append(t["variable_name"])

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
                self.vue["$data"].variables = js.python_to_js(vars)
        except:
            traceback.print_exc()


    def refresh_globals_table(self, *args):
        self.core.create_task(self.do_refresh_globals_table())
    
    def new_variable(self, *args):
        try:
            self.reset_new_variable()
                        
            self.vue["$bvModal"].show("new_variable_modal")
        except:
            traceback.print_exc()

    def reset_new_variable(self, *args):
        from ..plugins.variable_dialog import get_all_webui_browser_variable_dialog_infos
        dialog_infos = get_all_webui_browser_variable_dialog_infos()
        print(dialog_infos)

        select_values=[]
        for d1 in dialog_infos.values():
            for d2 in d1.values():
                v = ",".join([d2.variable_type] + d2.variable_tags)
                select_values.append({"value": v, "text": d2.display_name})

        self.vue["$data"].new_variable_type_select_options = js.python_to_js(select_values)
        if len(select_values) > 0:
            self.vue["$data"].new_variable_type_selected = select_values[0]["value"]
        self.vue["$data"].new_variable_name = ""        

    def handle_new_variable(self, *args):
        self.core.create_task(self.do_handle_new_variable())

    def handle_submit(self,*args):
        pass

    async def do_handle_new_variable(self):
        try:
            var_name = self.vue["$data"].new_variable_name
            m = re.match("^[a-zA-Z](?:\\w*[a-zA-Z0-9])?$", var_name)
            if not m:
                js.alert(f"The variable name \"{var_name}\" is invalid")
                return
            
            var_type1 = self.vue["$data"].new_variable_type_selected
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

    core.layout.layout.root.getItemsById("program")[0].addChild(js.python_to_js(procedure_list_panel_config))

    procedure_list_panel_obj = PyriProcedureListPanel(core, core.device_manager)

    program_panel = js.Vue.new(js.python_to_js({
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
                        "click .procedure_list_play": lambda e, value, row, d: procedure_list_panel_obj.procedure_run(row["procedure_name"]),
                        "click .procedure_list_open": lambda e, value, row, d: procedure_list_panel_obj.procedure_open(row["procedure_name"]),
                        "click .procedure_list_copy": lambda e, value, row, d: procedure_list_panel_obj.procedure_copy(row["procedure_name"]),
                        "click .procedure_list_info": lambda e, value, row, d: procedure_list_panel_obj.procedure_info(row["procedure_name"]),
                        "click .procedure_list_remove": lambda e, value, row, d: procedure_list_panel_obj.procedure_delete(row["procedure_name"])
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

    p = core.layout.layout.root.getItemsById("program")[0].getItemsById("procedure_list")
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

    core.layout.layout.root.getItemsById("program")[0].addChild(js.python_to_js(globals_list_panel_config))

    globals_list_panel_obj = PyriGlobalsListPanel(core, core.device_manager)

    globals_panel = js.Vue.new(js.python_to_js({
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
                        "click .globals_table_open": lambda e, value, row, d: globals_list_panel_obj.variable_open(row["variable_name"]),
                        "click .globals_table_copy": lambda e, value, row, d: globals_list_panel_obj.variable_copy(row["variable_name"]),
                        "click .globals_table_info": lambda e, value, row, d: globals_list_panel_obj.variable_info(row["variable_name"]),
                        "click .globals_table_remove": lambda e, value, row, d: globals_list_panel_obj.variable_delete(row["variable_name"]),
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

    core.layout.layout.root.getItemsById("program")[0].addChild(js.python_to_js(output_list_panel_config))

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
       
        core.layout.layout.root.getItemsById("program")[0].addChild(js.python_to_js(blockly_panel_config))
        res = core.layout.layout.root.getItemsById(f"procedure_blockly_{procedure_name}")[0].element.find("#procedure_blockly_component")[0]
                
        procedure_panel = js.Vue.new(js.python_to_js({
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

            iframe.setBlocklyXml(procedure_src.data)
        except:
            traceback.print_exc()

    def do_save(self, evt):
        iframe = self.core.layout.layout.root.getItemsById(f"procedure_blockly_{self.procedure_name}")[0]\
                .element.find("#procedure_blockly_iframe")[0].contentWindow

        blockly_xml = iframe.getBlocklyXml()

        async def s():
            try:
                variable_manager = self.device_manager.get_device_subscription("variable_storage").GetDefaultClient()
                await variable_manager.async_setf_variable_value("procedure",self.procedure_name,RR.VarValue(blockly_xml,"string"),None)
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
       
        core.layout.layout.root.getItemsById("program")[0].addChild(js.python_to_js(pyri_panel_config))
        res = core.layout.layout.root.getItemsById(f"procedure_pyri_{procedure_name}")[0].element.find("#procedure_pyri_component")[0]
                
        procedure_panel = js.Vue.new(js.python_to_js({
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
                "insert_function_ok": self.insert_function_ok
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
            res_io = io.TextIOWrapper(io.BytesIO(await res.arrayBuffer()),encoding="utf-8")
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

            self.vue["$data"].insert_function_options = js.python_to_js(opts)

            self.vue["$bvModal"].show("insert-function-modal")
        except:
            traceback.print_exc()

    def insert_function(self,evt):
        self.core.create_task(self.do_insert_function())

    def insert_function_selected_changed(self,value):
        if value is None:
            return

        try:
            v = self.all_functions[value]
            self.vue["$data"].insert_function_selected_doc = v["docstring"] or ""
        except:
            traceback.print_exc()

    def insert_function_ok(self,evt):
        try:
            value = self.vue["$data"].insert_function_selected
            if value is None:
                return
            v = self.all_functions[value]

            iframe = self._get_iframe()
            iframe.insertText(v["full_signature"])

        except:
            traceback.print_exc()

    def insert_function_hidden(self,*args):
        self.vue["$data"].insert_function_selected_doc = ""
        self.vue["$data"].insert_function_selected = None

    