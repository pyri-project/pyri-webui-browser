from fileinput import close
from typing import List, Dict, Callable, Any, Tuple, TYPE_CHECKING
from ..plugins.panel import PyriWebUIBrowserPanelInfo, PyriWebUIBrowserPanelPluginFactory
from .. import PyriWebUIBrowser
# from .devices_panel import add_devices_panel
# from. program_panel import add_program_panel
from ..golden_layout import PyriGoldenLayoutPanelConfig

_panel_infos = {
    "welcome": PyriWebUIBrowserPanelInfo(
        title="Welcome",
        description = "Welcome panel",
        panel_type = "welcome",
        panel_category = "help",
        component_type="pyri-welcome",
        priority=0
    ),
    "devices": PyriWebUIBrowserPanelInfo(
        title="Devices",
        description = "Devices panel",
        panel_type="devices",
        panel_category="devices",
        component_type="pyri-devices",
        priority=1000
    ),
    "procedure_list": PyriWebUIBrowserPanelInfo(
        title="Procedure List",
        description="List of procedures",
        panel_type="procedure_list",
        panel_category="program",
        component_type="pyri-procedure-list",
        priority=2000
    ),
    "globals_list": PyriWebUIBrowserPanelInfo(
        title="Globals List",
        description="List of global variables",
        panel_type="globals_list",
        panel_category="program",
        component_type="pyri-globals-list",
        priority=3000
    ),
    "procedure_output": PyriWebUIBrowserPanelInfo(
        title="Output",
        description="Procedure output panel",
        panel_type="procedure_output",
        panel_category="program",
        component_type="pyri-procedure-output",
        priority=4000
    ),
    "program_main": PyriWebUIBrowserPanelInfo(
        title="Main",
        description="Program main state machine panel",
        panel_type="program_main",
        panel_category="program",
        component_type="pyri-program-main",
        priority=5000
    )
    # "program": PyriWebUIBrowserPanelInfo(
    #     title="Program",
    #     panel_type="program",
    #     priority=4000
    # )
}

_panel_default_configs = {
    "welcome": PyriGoldenLayoutPanelConfig(
        component_type=_panel_infos["welcome"].component_type,
        panel_id = "welcome",
        panel_title = "Welcome",
        closeable= False
    ),
    "devices": PyriGoldenLayoutPanelConfig(
        component_type=_panel_infos["devices"].component_type,
        panel_id = "devices",
        panel_title = "Devices",
        closeable= False
    ),
    "procedure_list": PyriGoldenLayoutPanelConfig(
        component_type=_panel_infos["procedure_list"].component_type,
        panel_id = "procedure_list",
        panel_title = "Procedures",
        closeable= False
    ),
    "globals_list": PyriGoldenLayoutPanelConfig(
        component_type=_panel_infos["globals_list"].component_type,
        panel_id = "globals_list",
        panel_title = "Globals",
        closeable= False
    ),
    "procedure_output": PyriGoldenLayoutPanelConfig(
        component_type=_panel_infos["procedure_output"].component_type,
        panel_id = "procedure_output",
        panel_title = "Output",
        closeable= False
    ),
    "program_main": PyriGoldenLayoutPanelConfig(
        component_type=_panel_infos["program_main"].component_type,
        panel_id = "program_main_main",
        panel_title = "Main",
        closeable= False
    )
}

class PyriStandardPanelsWebUIBrowserPanelPluginFactory(PyriWebUIBrowserPanelPluginFactory):
    def __init__(self):
        super().__init__()

    def get_plugin_name(self) -> str:
        return "pyri-webui-browser"

    def get_panels_infos(self) -> Dict[str,PyriWebUIBrowserPanelInfo]:
        return _panel_infos

    def get_default_panels(self, layout_config: str = "default") -> List[Tuple[PyriWebUIBrowserPanelInfo, "PyriGoldenLayoutPanelConfig"]]:
        if layout_config.lower() == "default":
            return [
                (_panel_infos["welcome"], _panel_default_configs["welcome"]),
                (_panel_infos["devices"], _panel_default_configs["devices"]),
                (_panel_infos["procedure_list"], _panel_default_configs["procedure_list"]),
                (_panel_infos["globals_list"], _panel_default_configs["globals_list"]),
                (_panel_infos["procedure_output"], _panel_default_configs["procedure_output"]),
                (_panel_infos["program_main"], _panel_default_configs["program_main"])
            ]
        else:
            return []

def get_webui_browser_panel_factory():
    return PyriStandardPanelsWebUIBrowserPanelPluginFactory()
