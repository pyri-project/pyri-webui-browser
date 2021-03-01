from typing import Dict, Any
from .golden_layout import PyriGoldenLayout
from .plugins.panel import get_all_webui_browser_panels_infos, add_webui_browser_panel
import js
from RobotRaconteur.Client import *
from pyri.device_manager_client import DeviceManagerClient
import traceback
from pyri.util.robotraconteur import robotraconteur_data_to_plain

class PyriWebUIBrowser:

    def __init__(self, loop: "RobotRaconteur.WebLoop", config: Dict[str,Any]):
        self._loop = loop
        self._config = config
        self._layout = PyriGoldenLayout(self)
        self._seqno = 0
        self._device_manager = DeviceManagerClient(config["device_manager_url"],autoconnect=False)
        self._devices_states_obj_sub = None
        self._devices_states_wire_sub = None
        
        def set_devices_states(state, devices_states):
            state.devices_states = devices_states

        self._store = js.window.vuex_store_new({
            "state": {
                "devices_states": {}
            },
            "mutations":
            {
                "set_devices_states": set_devices_states
            }
        })

    @property
    def loop(self):
        return self._loop

    @property
    def layout(self):
        return self._layout

    @property
    def seqno(self):
        return self._seqno

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
        js.jQuery.find("#menuContainer")[0].removeAttribute('hidden')

        await self.load_plugin_panels()

        for i in range(100):
            if i > 50:
                js.window.alert("Could not connect to devices states service")
                return
            if "devices_states" in self._device_manager.get_device_names():
                break
            await RRN.AsyncSleep(0.1,None)
            await self.update_devices()

        self._device_manager.connect_device("variable_storage")        
        self._device_manager.connect_device("devices_states")

        self._devices_states_obj_sub = self._device_manager.get_device_subscription("devices_states")
        self._devices_states_wire_sub = self._devices_states_obj_sub.SubscribeWire("devices_states")

        # Run infinite update loop

        while True:
            await RRN.AsyncSleep(0.1,None)
            await self.update()

    async def update(self):
        self._seqno += 1

        if self._seqno == 500:
            self._loop.call_soon(self.update_devices())

        res, devices_states, _ = self._devices_states_wire_sub.TryGetInValue()

        if res:
            #print(f"devices_states seqno: {devices_states.seqno}")

            self._store.commit("set_devices_states", robotraconteur_data_to_plain(devices_states))

    async def update_devices(self):
        try:
            await RRN.AsyncSleep(0.02,None)
            await self._device_manager.async_refresh_devices(1)
        except:
            traceback.print_exc()

    @property
    def vuex_store(self):
        return self._store
