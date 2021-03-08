from typing import List, Dict, Callable, Any
from ..plugins.panel import PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
import importlib_resources
import js
import traceback

import numpy as np

class PyriJogPanel(PyriWebUIBrowserPanelBase):
    def __init__(self):
        self.vue = None
        self.mousedown = False

    def init_vue(self,vue):
        self.vue = vue

    def current_robot_options(self, vue, *args):
                
        robot_device_names = []

        for local_name in vue["$store"].state.active_device_names:
            
            try:
                device_infos = vue["$store"].state.device_infos[local_name]
            except KeyError:
                traceback.print_exc()
                continue
            try:                
                root_object_type = device_infos.device_info.root_object_type
                if root_object_type == "com.robotraconteur.robotics.robot.Robot":
                    robot_device_names.append({"value": local_name, "text": local_name})
                    continue
                root_object_implements = device_infos.device_info.root_object_implements
                if "com.robotraconteur.robotics.robot.Robot" in root_object_implements:
                    robot_device_names.append({"value": local_name, "text": local_name})
                    continue           
            except AttributeError:
                traceback.print_exc()
                continue

        return robot_device_names

    
    def watch_current_robot_options(self, new_value, *args):
        if new_value.length > 0:
            if self.vue["$data"].current_robot is None:
                self.vue["$data"].current_robot = new_value[0].value
        else:
            self.vue["$data"].current_robot = None

    def joint_state(self, vue, *args):
        
        current_robot = vue["$data"].current_robot
        if current_robot is None:
            return []

        ret = []
        joint_info = None
        joint_position = None
        try:
            joint_info = vue["$store"].state.device_infos[current_robot].extended_info["com.robotraconteur.robotics.robot.RobotInfo"].joint_info
        except AttributeError:
            #traceback.print_exc()
            pass
            
        except KeyError:
            #traceback.print_exc()
            pass

        if joint_info is None:
            return []      

        try:
            e_state = vue["$store"].state.devices_states.devices_states[current_robot].state
            if e_state is not None:
                for e in e_state:
                    if e.type == "com.robotraconteur.robotics.robot.RobotState":
                        joint_position = e.state_data.joint_position
        except AttributeError:
            traceback.print_exc()
        except KeyError:
            traceback.print_exc()

        

        for i in range(len(joint_info)):
            v = dict()
            if joint_info is not None:
                v["lower"]= f"{np.rad2deg(joint_info[i].joint_limits.lower):.2f}"
                v["upper"]= f"{np.rad2deg(joint_info[i].joint_limits.upper):.2f}"
            else:
                v["lower"] = "N/A"
                v["upper"] = "N/A"

            if joint_position is not None:
                try:
                    v["current"] = f"{np.rad2deg(joint_position[i]):.2f}"
                except KeyError:
                    v["current"] = "N/A"
            else:
                v["current"] = "N/A"
            
            ret.append(v)        
        return ret

    def current_robot_mode(self, vue, *args):
        current_robot = vue["$data"].current_robot
        if current_robot is None:
            return "Invalid"

        mode = "Invalid"

        try:
            e_state = vue["$store"].state.devices_states.devices_states[current_robot].state
            if e_state is not None:
                for e in e_state:
                    if e.type == "com.robotraconteur.robotics.robot.RobotState":
                        command_mode = e.state_data.command_mode

                        if command_mode < 0:
                            mode = "Error"
                        elif command_mode == 0:
                            mode = "Halt"
                        elif command_mode == 1:
                            mode = "Jog"
                        elif command_mode == 2:
                            mode = "Trajectory"
                        elif command_mode == 3:
                            mode = "Position Command"
                        elif command_mode == 4:
                            mode = "Velocity Command"
                        elif command_mode == 5:
                            mode = "Homing"
                        else:
                            mode = f"Unknown ({command_mode})"
        except AttributeError:
            traceback.print_exc()
        except KeyError:
            traceback.print_exc()

        return mode

    def jog_decrement_mousedown(self, joint_index):
        print(f"jog_decrement_mousedown: {joint_index}")

    def jog_increment_mousedown(self, joint_index):
        print(f"jog_increment_mousedown: {joint_index}")

    def set_jog_mode(self, evt):
        js.alert("Enable jog")

    def set_halt_mode(self, evt):
        js.alert("Enable jog")

    def mousedown_evt(self,evt):
        self.mousedown = True

    def mouseup_evt(self,evt):
        self.mousedown = False

    def mouseleave_evt(self,evt):
        self.mousedown = False


async def add_jog_panel(panel_type: str, core: PyriWebUIBrowser, parent_element: Any):

    assert panel_type == "jog"

    jog_panel_html = importlib_resources.read_text(__package__,"jog_panel.html")

    panel_config = {
        "type": "component",
        "componentName": "jog",
        "componentState": {},
        "title": "Jogging",
        "id": "jog",
        "isClosable": False
    }

    gl = core.layout.layout

    def register_jog_panel(container, state):
        container.getElement().html(jog_panel_html)

    core.layout.register_component("jog",register_jog_panel)

    core.layout.add_panel(panel_config)

    core.layout.add_panel_menu_item("jog", "Jogging")

    jog_panel_obj = PyriJogPanel()

    jog_panel = js.Vue.new({
        "el": "#jog_panel_component",
        "store": core.vuex_store,
        "data":
        {
            "current_robot": None
        },
        "methods":
        {
            "jog_decrement_mousedown": jog_panel_obj.jog_decrement_mousedown,
            "jog_increment_mousedown": jog_panel_obj.jog_increment_mousedown,
            "set_jog_mode": jog_panel_obj.set_jog_mode,
            "set_halt_mode": jog_panel_obj.set_halt_mode,
            "mousedown": jog_panel_obj.mousedown_evt,
            "mouseup": jog_panel_obj.mouseup_evt,
            "mouseleave": jog_panel_obj.mouseleave_evt
        },
        "computed": 
        {
            "current_robot_options": jog_panel_obj.current_robot_options,
            "joint_state": jog_panel_obj.joint_state,
            "current_robot_mode": jog_panel_obj.current_robot_mode
        },
        "watch":
        {
            "current_robot_options": jog_panel_obj.watch_current_robot_options
        }
    })

    jog_panel_obj.init_vue(jog_panel)

    return jog_panel_obj