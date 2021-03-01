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

        self._devices_states_value = None

        self._device_infos = dict()
        self._device_infos_update_running = False
        
        def set_devices_states(state, devices_states):
            state.devices_states = devices_states

        def set_active_device_names(state, device_names):
            current_devices = []
            current_devices_js = state.active_device_names
            
            for i in range(current_devices_js.length):
                current_devices.append(current_devices_js[i])            
            
            if set(current_devices) != set(device_names):
                state.active_device_names = device_names

        self._store = js.window.vuex_store_new({
            "state": {
                "devices_states": {},
                "active_device_names": []
            },
            "mutations":
            {
                "set_devices_states": set_devices_states,
                "set_active_device_names": set_active_device_names
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

        if self._seqno == 600:
            self._loop.call_soon(self.update_devices())

        res, devices_states, _ = self._devices_states_wire_sub.TryGetInValue()

        if res:
            self._store.commit("set_devices_states", robotraconteur_data_to_plain(devices_states))

            active_device_names = list(devices_states.devices_states.keys())
            self._store.commit("set_active_device_names", active_device_names)
            self._devices_states_value = devices_states
            
            self._update_device_infos(devices_states)

        else:
            self._devices_states_value = None

    async def update_devices(self):
        try:
            await RRN.AsyncSleep(0.02,None)
            await self._device_manager.async_refresh_devices(1)
        except:
            traceback.print_exc()

    @property
    def vuex_store(self):
        return self._store

    @property
    def devices_states(self):
        return self._devices_states_value

    def _update_device_infos(self,devices_states):
        try:
            if self._device_infos_update_running:
                return

            update_devices = []

            for d in devices_states.devices_states.keys():
                if d not in self._device_infos:
                    self._device_infos[d] = dict()
                
                if len(self._device_infos[d]) != 3:
                    update_devices.append(d)
                    
            if len(update_devices) > 0:
                self._loop.call_soon(self._do_update_device_infos(update_devices))
        except:
            traceback.print_exc()


    async def _do_update_device_infos(self,local_device_names):
        try:
            self._device_infos_update_running = True
            states_connected, states = self._devices_states_obj_sub.TryGetDefaultClient()
            for d in local_device_names:
                if not "device_info" in self._device_infos[d]:
                    self._device_infos[d]["device_info"] = self._device_manager.get_device_info(d)
                if self._devices_states_value.devices_states[d].connected and states_connected:
                    if not "standard_info" in self._device_infos[d]:
                        try:
                            self._device_infos[d]["standard_info"] = await states.async_getf_standard_device_info(d,None)
                        except:
                            traceback.print_exc()
                    
                    if not "extended_info" in self._device_infos[d]:
                        try:
                            self._device_infos[d]["extended_info"] = await states.async_getf_extended_device_info(d,None)
                        except:
                            traceback.print_exc()

        finally:
            self._device_infos_update_running = False

            print(self._device_infos)

