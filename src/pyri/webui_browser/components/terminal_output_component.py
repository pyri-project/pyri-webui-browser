from typing import List, Dict, Callable, Any, Union, Tuple
import importlib_resources
import js
import traceback

from ..util import to_js2

from ..pyri_vue import PyriVue, VueComponent, vue_register_component, vue_data, vue_method

@VueComponent
class PyriTerminalOutputComponent(PyriVue):

    vue_template = importlib_resources.read_text(__package__, "terminal_output_component.html")

    output_lines = vue_data([])

    def append_output_line(self, output_line: str, text_css_class: str = None):
        # Use JS lines directly
        output_lines_js = self.output_lines
        output_lines_js.push(to_js2({
            "text": output_line,
            "text_class": text_css_class or ""
        }))
        #self.output_lines = output_lines_js

    def append_output_lines(self, output_lines: Union[List[str],List[Tuple[str,str]]]):
        if len(output_lines) == 0:
            return
        # Use JS lines directly
        output_lines_js = self.output_lines
        for l in output_lines:
            if not isinstance(l, tuple):
                output_lines_js.push(to_js2({
                    "text": str(l),
                    "text_class": ""
                }))
            else:
                 output_lines_js.push(to_js2({
            "text": l[0],
            "text_class": l[1] if len(l) > 1 else ""
        }))
        #self.output_lines = output_lines_js

    def clear_output(self):
        self.output_lines = to_js2([])

def register_vue_components():
    vue_register_component("pyri-terminal-output", PyriTerminalOutputComponent)
