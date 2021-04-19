from typing import List, Dict, Callable, Any
from ..plugins.panel import PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
import importlib_resources
import js
import traceback
from RobotRaconteur.Client import *
import random
import re

async def run_procedure(device_manager, name):
    try:
        c = device_manager.get_device_subscription("sandbox").GetDefaultClient()
        gen = await c.async_execute_procedure(name, [], None)

        res = await gen.AsyncNext(None,None)
        await gen.AsyncClose(None)

        res_printed = '\n'.join(res.printed)
        js.window.alert(f"Run procedure {name} complete:\n\n{res_printed}")
        
    except Exception as e:
        
        js.window.alert(f"Run procedure {name} failed:\n\n{traceback.format_exc()}" )


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
        self.core.create_task(run_procedure(self.device_manager,name))

    def procedure_open(self, name):
        p = PyriBlocklyProgramPanel(name,self.core,self.device_manager)


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
        "store": core.vuex_store,
        "data":
        {
            "procedures": []
        },
        "methods":
        {
            "procedure_run": procedure_list_panel_obj.procedure_run,
            "procedure_open": procedure_list_panel_obj.procedure_open,
            "procedure_copy": procedure_list_panel_obj.procedure_copy,
            "procedure_info": procedure_list_panel_obj.procedure_info,
            "procedure_delete": procedure_list_panel_obj.procedure_delete,
            "refresh_procedure_table": procedure_list_panel_obj.refresh_procedure_table,
            "new_blockly_procedure": procedure_list_panel_obj.new_blockly_procedure
        }
    }))

    procedure_list_panel_obj.init_vue(program_panel)

    blockly_panel_html = importlib_resources.read_text(__package__,"procedure_blockly_panel.html")

    def register_blockly_panel(container, state):
        container.getElement().html(blockly_panel_html)

    core.layout.register_component(f"procedure_blockly",register_blockly_panel)

    add_globals_panel(core)

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
        "store": core.vuex_store,
        "data":
        {
            "variables": [],
            "new_variable_type_selectedState": "",
            "new_variable_type_selected": "",
            "new_variable_name_inputState": "",
            "new_variable_name": "",
            "new_variable_type_select_options": []
        },
        "methods":
        {            
            "variable_open": globals_list_panel_obj.variable_open,
            "variable_copy": globals_list_panel_obj.variable_copy,
            "variable_info": globals_list_panel_obj.variable_info,
            "variable_delete": globals_list_panel_obj.variable_delete,
            "refresh_globals_table": globals_list_panel_obj.refresh_globals_table,
            "new_variable": globals_list_panel_obj.new_variable,
            "reset_new_variable": globals_list_panel_obj.reset_new_variable,
            "handle_new_variable": globals_list_panel_obj.handle_new_variable,
            "handle_submit": globals_list_panel_obj.handle_submit

        }
    }))

    globals_list_panel_obj.init_vue(globals_panel)

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
            "store": core.vuex_store,
            "data":
            {
                "procedure_name": procedure_name
            },
            "methods":
            {
                "save": self.do_save,
                "run": self.do_run,
                "iframe_load": self.iframe_loaded
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
        self.core.create_task(run_procedure(self.device_manager,self.procedure_name))