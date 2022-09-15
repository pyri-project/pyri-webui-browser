from typing import List, Dict, Callable, Any
import importlib_resources
from RobotRaconteur.Client import *
from ..pyri_vue import PyriVue, VueComponent, vue_register_component

@VueComponent
class PyriWelcomePanel(PyriVue):

    vue_template = importlib_resources.read_text(__package__,"welcome_panel.html")

    def __init__(self):
        super().__init__()

def register_vue_components():
    vue_register_component('pyri-welcome', PyriWelcomePanel)