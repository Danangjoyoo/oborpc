"""
"""
import inspect
from ._base import OBORBuilder


class ServerBuilder(OBORBuilder):
    def __init__(self, host, port=None, timeout=1, retry=0) -> None:
        super().__init__(host, port, timeout, retry)

    def create_remote_responder(self, instance, router, class_name, method_name, method):
        raise NotImplementedError("method should be overridden")

    def dispatch_rpc_request(self, instance, method, body):
        args = body.get("args", [])
        kwargs = body.get("kwargs", {})
        res = method(instance, *args, **kwargs)
        return {"data": res}

    def setup_server_rpc(self, instance: object, router):
        _class = instance.__class__
        iterator_class = instance.__class__.__base__
        method_map = {
            name: method for (name, method) in inspect.getmembers(
                _class, predicate=inspect.isfunction
            )
        }

        for (name, method) in inspect.getmembers(iterator_class, predicate=inspect.isfunction):
            if name not in iterator_class.__oborprocedures__:
                continue
            self.create_remote_responder(instance, router, iterator_class.__name__, name, method_map.get(name))
