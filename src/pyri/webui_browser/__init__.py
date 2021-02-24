from typing import Dict, Any
from .golden_layout import PyriGoldenLayout
from .plugins.panel import get_all_webui_browser_panels_infos, add_webui_browser_panel

class PyriWebUIBrowser:

    def __init__(self, loop: "RobotRaconteur.WebLoop", config: Dict[str,Any]):
        self._loop = loop
        self._config = config
        self._layout = PyriGoldenLayout(self)


    @property
    def loop(self):
        return self._loop

    @property
    def layout(self):
        return self._layout

    async def load_plugin_panels(self):
        all_panels_u = get_all_webui_browser_panels_infos()
        all_panels = dict()
        for u in all_panels_u.values():
            all_panels.update(u)

        all_panels_sorted = sorted(all_panels.values(), key=lambda x: x.priority)

        for p in all_panels_sorted:
            await add_webui_browser_panel(p.panel_type, self, self._layout.layout_container)

    async def run(self):
        print("Running PyRI WebUI Browser")

        self._layout.init_golden_layout()

        await self.load_plugin_panels()


