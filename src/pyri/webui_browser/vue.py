import asyncio
from typing import Dict, Any, Callable, Union
import js

from pyodide import create_once_callable, create_proxy, to_js, run_js
import inspect
import traceback
import sys

def to_js2(val):
    return to_js(val,dict_converter=js.Object.fromEntries)

_wrap_js_this = run_js("""(function () {
                                return function (fn)
                                {
                                    return (function (...args){
                                        return fn(this,...args);
                                    })
                                }
                            })()""")

def vue_method(fn, vue_method_name = None):
    if vue_method_name is None:
        vue_method_name = fn.__name__
    fn._vue_method = vue_method_name
    return fn

def vue_computed(fn, vue_computed_name = None):
    if vue_computed_name is None:
        vue_computed_name = fn.__name__
    fn._vue_computed = vue_computed_name
    return fn

def vue_watch(vue_watch_property, vue_watch_deep = None, vue_watch_immediate = None, vue_watch_flush = None):
    def vue_watch_inner(fn):
        fn._vue_watch_property = vue_watch_property
        if vue_watch_deep is not None:
            fn._vue_watch_deep = vue_watch_deep
        if vue_watch_immediate is not None:
            fn._vue_watch_immediate = vue_watch_immediate
        if vue_watch_flush is not None:
            fn._vue_watch_flush = vue_watch_flush
        return fn
    return vue_watch_inner

class vue_data():
    def __init__(self, init_value = None):
        self._vue_data = None
        self._init_value = init_value

    def __get__(self, instance, owner = None):
        if instance is None:
            return self
        return instance._vue_get_data(self._vue_data)

    def __set__(self, instance, value):
        instance._vue_set_data(self._vue_data, value)

    def __delete__(self, instance):
        return

class vue_prop():
    def __init__(self):
        self._vue_prop = None

    def __get__(self, instance, owner = None):
        if instance is None:
            return self
        return instance._vue_get_prop(self._vue_prop)

    def __set__(self, instance, value):
        raise AttributeError("Props are read only")

    def __delete__(self, instance):
        raise AttributeError("Props are read only")

def _vue_method_proxy(fn):

    def run_method(js_this, *args):
        py_obj = getattr(js_this,"$data").py_obj
        if py_obj is None:
            return None
        res = fn(py_obj,*args)
        if inspect.isawaitable(res):
            async def run_async_method():
                try:
                    await res
                except BaseException as exp:
                    py_obj._vue_handle_async_exception(exp)
            return py_obj._vue_create_task(run_async_method())
        else:
            return res


    return _wrap_js_this(create_proxy(run_method))

def _vue_get_methods(vue_class: type):
    methods = {}
    for a in dir(vue_class):
        a1 = getattr(vue_class, a)
        if hasattr(a1,"_vue_method"):
            methods[a1._vue_method] = _vue_method_proxy(a1)
    return methods

def _vue_get_data(vue_class: type):
    data = {}
    for a in dir(vue_class):
        a1 = getattr(vue_class, a)
        if hasattr(a1,"_vue_data"):
            a1._vue_data = a
            data[a1._vue_data] = a1
    def _new_data(*args):
        ret = {}
        for k,v in data.items():
            if inspect.isfunction(v):
                ret[k] = v._init_value(*args)
            else:
                ret[k] = v._init_value
        ret["py_obj"] = None
        return to_js2(ret)
    return _new_data

def _vue_get_props(vue_class: type):
    props = []
    for a in dir(vue_class):
        a1 = getattr(vue_class, a)
        if hasattr(a1,"_vue_prop"):
            a1._vue_prop = a
            props.append(a)
    return props

def _vue_get_computed(vue_class: type):
    methods = {}
    for a in dir(vue_class):
        a1 = getattr(vue_class, a)
        if hasattr(a1,"_vue_computed"):
            methods[a1._vue_computed] = _vue_method_proxy(a1)
    return methods

def _vue_get_watch(vue_class: type):
    watch = {}
    for a in dir(vue_class):
        a1 = getattr(vue_class, a)
        if hasattr(a1,"_vue_watch_property"):
            w = { "handler": _vue_method_proxy(a1) }
            if hasattr(a1,"_vue_watch_deep"):
                w["deep"] = a1._vue_watch_deep
            if hasattr(a1,"_vue_watch_immediate"):
                w["immediate"] = a1._vue_watch_immediate
            if hasattr(a1,"_vue_watch_flush"):
                w["flush"] = a1._vue_watch_flush
            watch[a1._vue_watch_property] = w
    return watch


class Vue:
    def __init__(self, el: Union["js.JsProxy",str] = None):
        if self._vue_class is None:
            vue_methods = _vue_get_methods(type(self))
            vue_data = _vue_get_data(type(self))
            vue_computed = _vue_get_computed(type(self))
            vue_watch = _vue_get_watch(type(self))            

            components = type(self).vue_components

            components_vue = {k: v._vue_class for k,v in components.items()}

            self._vue = js.Vue.new(to_js2(
                {
                    "el": el,
                    "components": to_js2(components_vue),
                    "data": to_js2(vue_data),
                    "methods": to_js2(vue_methods),
                    "created": _vue_method_proxy(type(self).before_mount),
                    "beforeMount": _vue_method_proxy(type(self).before_mount),
                    "mounted": _vue_method_proxy(type(self).mounted),
                    "beforeDestray": _vue_method_proxy(type(self).before_destroy),
                    "computed": to_js2(vue_computed),
                    "watch": to_js2(vue_watch)
                })
            )

            getattr(self.vue,"$data").py_obj = self

    @property
    def vue(self):
        return self._vue

    def destroy(self):
        self.vue.destroy()

    def _vue_get_data(self, data_name):
        return getattr(getattr(self.vue, "$data"),data_name)

    def _vue_set_data(self, data_name, value):
        return setattr(getattr(self.vue, "$data"),data_name,value)

    def _vue_get_prop(self, prop_name):
        return getattr(getattr(self.vue, "$props"),prop_name)

    def _vue_set_prop(self, prop_name, value):
        return setattr(getattr(self.vue, "$props"),prop_name,value)

    def _vue_create_task(self, task):
        loop = asyncio.get_event_loop()
        return loop.create_task(task)

    def _vue_handle_async_exception(self, exp):
        print(f"Uncaught exception in async task: {traceback.format_exception(exp)}", file=sys.stderr)

    _vue_class = None

    def created(self):
        pass

    def before_mount(self):
        pass

    def mounted(self):
        pass

    def before_destroy(self):
        pass

    @property
    def emit(self):
        return getattr(self.vue,"$emit")

    @property
    def on(self):
        return getattr(self.vue,"$on")

    @property
    def refs(self):
        return getattr(self.vue,"$refs")

    def get_ref_pyobj(self, ref_name):
        return getattr(getattr(self.refs,ref_name),"$data").py_obj

    @property
    def bvModal(self):
        return getattr(self.vue,"$bvModal")

    def next_tick(self):
        return getattr(self.vue,"$nextTick")()

    @property
    def watch(self):
        return getattr(self.vue,"$watch")

    vue_template = None

    vue_components = {}

def VueComponent(vue_py_class):
    vue_methods = _vue_get_methods(vue_py_class)
    vue_data = _vue_get_data(vue_py_class)
    vue_props = _vue_get_props(vue_py_class)
    vue_computed = _vue_get_computed(vue_py_class)
    vue_watch = _vue_get_watch(vue_py_class)

    components = vue_py_class.vue_components

    vue_components = {k: v._vue_class for k,v in components.items()}
    
    def component_created(js_this):
        py_obj = vue_py_class()
        py_obj._vue = js_this
        getattr(js_this,"$data").py_obj = py_obj        
        py_obj.created()

    vue_py_class._vue_class = js.Vue.extend(to_js2(
        {
            "template": vue_py_class.vue_template,
            "data": to_js2(vue_data),
            "methods": to_js2(vue_methods),
            "props": to_js2(vue_props),
            "created": _wrap_js_this(create_proxy(component_created)),
            "beforeMount": _vue_method_proxy(vue_py_class.before_mount),
            "mounted": _vue_method_proxy(vue_py_class.mounted),
            "beforeDestroy": _vue_method_proxy(vue_py_class.before_destroy),
            "computed": to_js2(vue_computed),
            "components": to_js2(vue_components),
            "watch": to_js2(vue_watch)
            
        })
    )

    return vue_py_class

