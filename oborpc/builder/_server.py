"""
Server Builder Base
"""
import inspect
from ._base import OBORBuilder


class ServerBuilder(OBORBuilder):
    """
    Server Builder
    """
    def create_remote_responder(self, instance, router, class_name, method_name, method): # pylint: disable=too-many-arguments
        """
        Remote RPC Request Responder
        """
        raise NotImplementedError("method should be overridden")

    def create_remote_responder_async(self, instance, router, class_name, method_name, method): # pylint: disable=too-many-arguments
        """
        Remote RPC Request Responder Async
        """
        raise NotImplementedError("method should be overridden")

    def dispatch_rpc_request(self, instance, method, body):
        """
        Dispatch RPC Request
        """
        args = body.get("args", [])
        kwargs = body.get("kwargs", {})
        res = method(instance, *args, **kwargs)
        return {"data": res}

    async def dispatch_rpc_request_async(self, instance, method, body):
        """
        Dispatch RPC Request
        """
        args = body.get("args", [])
        kwargs = body.get("kwargs", {})
        res = await method(instance, *args, **kwargs)
        return {"data": res}

    def setup_server_rpc(self, instance: object, router):
        """
        Setup RPC Server
        """
        _class = instance.__class__
        iterator_class = instance.__class__.__base__
        method_map = { # pylint: disable=unnecessary-comprehension
            name: method for (name, method) in inspect.getmembers(
                _class, predicate=inspect.isfunction
            )
        }

        for (name, method) in inspect.getmembers(iterator_class, predicate=inspect.isfunction):
            if name not in iterator_class.__oborprocedures__:
                continue
            method = method_map.get(name)
            if inspect.iscoroutinefunction(method):
                self.create_remote_responder_async(
                    instance, router, iterator_class.__name__,
                    name, method
                )
            else:
                self.create_remote_responder(
                    instance, router, iterator_class.__name__,
                    name, method
                )
