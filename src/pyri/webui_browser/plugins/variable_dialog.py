from typing import List, Dict, Callable, Any, NamedTuple, Tuple, TYPE_CHECKING
from pyri.plugins import util as plugin_util

if TYPE_CHECKING:
    from .. import PyriWebUIBrowser

class PyriWebUIBrowserVariableDialogInfo(NamedTuple):
    name: str
    display_name: str
    variable_type: str
    variable_tags: List[str]
    doc: str

class PyriWebUIBrowserVariableDialogBase:
    pass

class PyriWebUIBrowserVariableDialogPluginFactory:
    def __init__(self):
        super().__init__()

    def get_plugin_name(self) -> str:
        return ""

    def get_variable_dialog_infos(self) -> Dict[Tuple[str,Tuple[str]],PyriWebUIBrowserVariableDialogInfo]:
        return []

    def show_variable_new_dialog(self, new_name: str, variable_type: str, variable_tags: str, core: "PyriWebUIBrowser") -> None:
        raise NotImplementedError()

    def show_variable_edit_dialog(self, variable_name: str, variable_type: str, variable_tags: List[str], core: "PyriWebUIBrowser") -> None:
        raise NotImplementedError()

def get_webui_browser_variable_dialog_factories() -> List[PyriWebUIBrowserVariableDialogPluginFactory]:
    return plugin_util.get_plugin_factories("pyri.plugins.webui_browser_variable_dialog")

def get_all_webui_browser_variable_dialog_infos() -> Dict[str,Any]:
    ret = dict()
    factories = get_webui_browser_variable_dialog_factories()
    for factory in factories:
        ret[factory.get_plugin_name()] = factory.get_variable_dialog_infos()
    return ret

def get_all_webui_variable_new_options() -> Dict[str,str]:
    infos = get_all_webui_browser_variable_dialog_infos()
    ret = dict()
    for i in infos:
        for i2 in i.values():
            ret[i2.display_name] = (i2.variable_type,i2.variable_tags)
    return ret

def show_webui_browser_variable_new_dialog(new_name: str, variable_type: str, variable_tags: List[str], core: "PyriWebUIBrowser") -> None:
    
    factories = get_webui_browser_variable_dialog_factories()
    for factory in factories:
        infos = factory.get_variable_dialog_infos()
        for v in infos.values():
            if v.variable_type == variable_type and set(v.variable_tags).issubset(set(variable_tags)):
                factory.show_variable_new_dialog(new_name, variable_type, variable_tags, core)
                return

    assert False, f"Unknown variable_type \"{variable_type},{variable_tags}\" specified"

def show_webui_browser_variable_edit_dialog(variable_name: str, variable_type: str, variable_tags: List[str], core: "PyriWebUIBrowser") -> None:
    
    factories = get_webui_browser_variable_dialog_factories()
    for factory in factories:
        infos = factory.get_variable_dialog_infos()
        if variable_type in infos:
            factory.show_variable_edit_dialog(variable_name, variable_type, core)
            return

    assert False, f"Unknown variable_type \"{variable_type},{variable_tags}\" specified"