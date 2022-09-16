from ..plugins.component import PyriWebUIBrowserComponentPluginFactory
from .welcome_component import register_vue_components as welcome_register_vue_components
from .devices_component import register_vue_components as devices_register_vue_components
from .procedure_list_component import register_vue_components as procedure_list_register_vue_components
from .globals_list_component import register_vue_components as globals_list_register_vue_components
from .terminal_output_component import register_vue_components as terminal_output_register_vue_components
from .procedure_output_component import register_vue_components as procedure_output_register_vue_components
from .program_main_component import register_vue_components as program_main_register_vue_components
from .procedure_pyri_component import register_vue_components as pyri_register_vue_components
from .procedure_blockly_component import register_vue_components as blockly_register_vue_components

class PyriStandardComponentsWebUIBrowserComponentPluginFactory(PyriWebUIBrowserComponentPluginFactory):
    def get_plugin_name(self) -> str:
        return "pyri-webui-browser"

    def register_components(self) -> None:
        welcome_register_vue_components()
        devices_register_vue_components()
        procedure_list_register_vue_components()
        globals_list_register_vue_components()
        terminal_output_register_vue_components()
        procedure_output_register_vue_components()
        program_main_register_vue_components()
        pyri_register_vue_components()
        blockly_register_vue_components()

def get_webui_browser_component_factory():
    return PyriStandardComponentsWebUIBrowserComponentPluginFactory()