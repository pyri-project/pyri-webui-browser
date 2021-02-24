import js
import json

_golden_layout_config = {
    "settings":{
        "hasHeaders": True,
        "constrainDragToContainer": True,
        "reorderEnabled": True,
        "selectionEnabled": False,
        "popoutWholeStack": False,
        "blockedPopoutsThrowError": True,
        "closePopoutsOnUnload": True,
        "showPopoutIcon": False, 
        "showMaximiseIcon": True,
        "showCloseIcon": False
    },
    "dimensions": 
    {
        "borderWidth": 15,
        "minItemHeight": 10,
        "minItemWidth": 10,
        "headerHeight": 30,
        "dragProxyWidth": 300,
        "dragProxyHeight": 200
    },
    "labels": 
    {
        "close": 'close',
        "maximise": 'maximise',
        "minimise": 'minimise',
        "popout": 'open in new window'
    },
    "content":
    [
        {
            "type": "stack",
            "content": [
            ]
        }
    ]
}

class PyriGoldenLayout:
    def __init__(self,core):
        self._core = core
        self._layout = None

    def init_golden_layout(self):
        
        layoutContainer = js.jQuery.find("#layoutContainer")
        self._layout =js.golden_layout_new(_golden_layout_config, layoutContainer)


        self._layout.init()

        js.jQuery(js.window).resize(lambda _: self._layout.updateSize())

    @property
    def layout_container(self):
        return js.jQuery.find("#layoutContainer")

    @property
    def layout(self):
        return self._layout

    def register_component(self,name,constructor_function,py_this=None):
        js.golden_layout_register_component(self._layout,name,constructor_function,py_this)

    def add_panel(self,panel_config):
        self._layout.root.contentItems[0].addChild(panel_config)

    def add_panel_menu_item(self,panel_id, text_label):
        menu_item = js.golden_layout_append_menu_item(text_label)
        
        def menu_click(evt):
            p = self._layout.root.contentItems[0].getItemsById(panel_id)
            if len(p) > 0:
                p[0].parent.setActiveContentItem(p[0])
            
        

        menu_item.click(menu_click)

