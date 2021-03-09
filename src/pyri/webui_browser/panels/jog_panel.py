from typing import List, Dict, Callable, Any
from ..plugins.panel import PyriWebUIBrowserPanelBase
from .. import PyriWebUIBrowser
import importlib_resources
import js
import traceback

import numpy as np

def R2rpy(R):
    assert np.linalg.norm(R[0:2,0]) > np.finfo(float).eps * 10.0, "Singular rpy requested"
    
    r=np.arctan2(R[2,1],R[2,2])
    y=np.arctan2(R[1,0], R[0,0])
    p=np.arctan2(-R[2,0], np.linalg.norm(R[2,1:3]))
        
    return (r,p,y)

def q2R(q):
   
    I = np.identity(3)
    qhat = hat(q[1:4])
    qhat2 = qhat.dot(qhat)
    return I + 2*q[0]*qhat + 2*qhat2

def hat(k):
    khat=np.zeros((3,3))
    khat[0,1]=-k[2]
    khat[0,2]=k[1]
    khat[1,0]=k[2]
    khat[1,2]=-k[0]
    khat[2,0]=-k[1]
    khat[2,1]=k[0]    
    return khat

class PyriJogPanel(PyriWebUIBrowserPanelBase):
    def __init__(self, device_manager, core):
        self.vue = None
        self.mousedown = False
        self.device_manager = device_manager
        self.core = core
        self.jog_connected = False

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

    async def get_jog(self):
        
        #TODO: Fix connect_device("joint_jog")
        if not self.jog_connected:
            self.device_manager.connect_device("joint_jog")
            self.device_manager.connect_device("cartesian_jog")
            self.jog_connected = True
            
        current_robot = self.vue["$data"].current_robot
        if current_robot is None:
            return None, None
        try:
            jog_service = await self.device_manager.get_device_subscription("joint_jog").AsyncGetDefaultClient(None,timeout=1)
        except:
            return None, None
        joint_jog =  await jog_service.async_get_jog(current_robot,None)

        cart_jog = None
        try:
            cart_jog_service = await self.device_manager.get_device_subscription("cartesian_jog").AsyncGetDefaultClient(None,timeout=1)
            cart_jog =  await cart_jog_service.async_get_jog(current_robot,None)
            
        except:
            traceback.print_exc()

        print(f"joint_jog: {joint_jog}, cart_jog: {cart_jog}")
        return joint_jog, cart_jog

    def jog_joints(self,q_i, sign):
        # @burakaksoy RR-Client-WebBrowser-Robot.py:380
        self.core.loop.create_task(self.async_jog_joints(q_i, sign))

    async def async_jog_joints(self, q_i, sign):
        try:
            # @burakaksoy RR-Client-WebBrowser-Robot.py:391
            jog, _ = await self.get_jog()
            while (self.mousedown): 
                # Call Jog Joint Space Service funtion to handle this jogging
                # await plugin_jogJointSpace.async_jog_joints2(q_i, sign, None)
                await jog.async_jog_joints3(q_i, sign, None)

            #await plugin_jogJointSpace.async_stop_joints(None)
        except:
            traceback.print_exc()
        
    def jog_decrement_mousedown(self, joint_index):
        self.jog_joints(joint_index+1,-1)

    def jog_increment_mousedown(self, joint_index):
        self.jog_joints(joint_index+1,+1)

    async def do_set_jog_mode(self):
        try:
            jog, cart_jog = await self.get_jog()
            if jog is None:
                return
            await jog.async_setf_jog_mode(None)
            #await cart_jog.async_prepare_jog(None)
        except:
            traceback.print_exc()

    def set_jog_mode(self, evt):
        self.core.create_task(self.do_set_jog_mode())

    def set_halt_mode(self, evt):
        self.core.create_task(self.do_set_halt_mode())
    
    async def do_set_halt_mode(self):
        try:
            jog, cart_jog = await self.get_jog()
            if jog is None:
                return
            await jog.async_setf_halt_mode(None)
        except:
            traceback.print_exc()

    def mousedown_evt(self,evt):
        self.mousedown = True

    def mouseup_evt(self,evt):
        self.mousedown = False

    def mouseleave_evt(self,evt):
        self.mousedown = False

    def jog_cart_decrement_mousedown(self, joint_index):
        #self.jog_joints(joint_index+1,-1)
        print(f"jog_cart_decrement_mousedown: {joint_index}")

    def jog_cart_increment_mousedown(self, joint_index):
        #self.jog_joints(joint_index+1,+1)
        print(f"jog_cart_increment_mousedown: {joint_index}")

    def jog_cartesian(P_axis, R_axis):
        # @burakaksoy RR-Client-WebBrowser-Robot.py:508
        global is_mousedown
        is_mousedown = True

        global is_jogging
        if (not is_jogging): 
            is_jogging = True
            loop.create_task(async_jog_cartesian(P_axis, R_axis))
        else:
            print_div("Jogging has not finished yet..<br>")

    async def async_jog_cartesian(P_axis, R_axis):
        # @burakaksoy RR-Client-WebBrowser-Robot.py:520
        global plugin_jogCartesianSpace
        await plugin_jogCartesianSpace.async_prepare_jog(None)
        # await plugin_jogCartesianSpace.async_jog_cartesian(P_axis, R_axis, None)
        
        global is_mousedown
        while (is_mousedown):
            # Call Jog Cartesian Space Service funtion to handle this jogging
            # await plugin_jogCartesianSpace.async_jog_cartesian(P_axis, R_axis, None)
            await plugin_jogCartesianSpace.async_jog_cartesian2(P_axis, R_axis, None)

        await plugin_jogCartesianSpace.async_stop_joints(None)
        global is_jogging
        is_jogging = False

    def cur_ZYX_angles(self, vue, *args):
        current_robot = vue["$data"].current_robot
        if current_robot is None:
            return ""

        current_rpy = ""
        try:
            e_state = vue["$store"].state.devices_states.devices_states[current_robot].state
            if e_state is not None:
                for e in e_state:
                    if e.type == "com.robotraconteur.robotics.robot.RobotState":
                        
                        current_rpy = np.array2string(np.rad2deg(R2rpy(q2R(np.array([e.state_data.kin_chain_tcp[0][0][x] for x in range(4)],dtype=np.float64)))),formatter={'float_kind':lambda x: "%.2f" % x})
        except AttributeError:
            traceback.print_exc()
        except KeyError:
            traceback.print_exc()

        return current_rpy

    def cur_position(self, vue, *args):

        current_robot = vue["$data"].current_robot
        if current_robot is None:
            return ""

        current_position = ""
        try:
            e_state = vue["$store"].state.devices_states.devices_states[current_robot].state
            if e_state is not None:
                for e in e_state:
                    if e.type == "com.robotraconteur.robotics.robot.RobotState":
                        current_position = np.array2string(np.array([e.state_data.kin_chain_tcp[0][1][x] for x in range(3)],dtype=np.float64), formatter={'float_kind':lambda x: "%.2f" % x})
        except AttributeError:
            traceback.print_exc()
        except KeyError:
            traceback.print_exc()

        return current_position


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

    jog_panel_obj = PyriJogPanel(core.device_manager,core)

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
            "mouseleave": jog_panel_obj.mouseleave_evt,
            "jog_cart_decrement_mousedown": jog_panel_obj.jog_cart_decrement_mousedown,
            "jog_cart_increment_mousedown": jog_panel_obj.jog_cart_increment_mousedown,

        },
        "computed": 
        {
            "current_robot_options": jog_panel_obj.current_robot_options,
            "joint_state": jog_panel_obj.joint_state,
            "current_robot_mode": jog_panel_obj.current_robot_mode,
            "cur_ZYX_angles": jog_panel_obj.cur_ZYX_angles,
            "cur_position": jog_panel_obj.cur_position
        },
        "watch":
        {
            "current_robot_options": jog_panel_obj.watch_current_robot_options
        }
    })

    jog_panel_obj.init_vue(jog_panel)

    return jog_panel_obj