from copy import copy

class JsBindDecorator:
    def __init__(self, f):
        self._f = f
        self._js_this = None
        self.instance = None

    def bind(self, js_this):
        self._js_this = js_this
        return self

    def __call__(self, *args, **kwargs):
        self._f(self.instance,self._js_this, *args, **kwargs)

    def __get__(self, instance, owner):
        # self here is the instance of "somewrapper"
        # and "instance" is the instance of the class where
        # the decorated method is.
        if instance is None:
            return self
        bound_callable = copy(self)
        bound_callable.instance = instance
        return bound_callable

    

def jsbind(f):
    return JsBindDecorator(f)