"""
Server Builder Base
"""
import inspect


class ServerBuilder:
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

    def setup_server_rpc(self, instance: object, router, secure_build: bool = True):
        """
        Setup RPC Server
        """
        _class = instance.__class__
        method_map = { # pylint: disable=unnecessary-comprehension
            name: method for (name, method) in inspect.getmembers(
                _class, predicate=inspect.isfunction
            )
        }

        iterator_class = instance.__class__.__base__
        iterator_method_map = { # pylint: disable=unnecessary-comprehension
            name: method for (name, method) in inspect.getmembers(
                iterator_class, predicate=inspect.isfunction
            )
        }

        for (name, method) in inspect.getmembers(iterator_class, predicate=inspect.isfunction):
            if name not in iterator_class.__oborprocedures__:
                continue

            # validate
            method = method_map.get(name)
            iterator_method = iterator_method_map.get(name)
            if secure_build:
                self.validate_implementation(name, method, _class, iterator_method, iterator_class)

            # build router
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

    def validate_implementation(
        self,
        method_name,
        implementation_method,
        implementation_class,
        origin_method,
        origin_class,
    ):
        # validate implementation: check overridden procedure
        method_str = str(implementation_method)
        method_origin = method_str[9:method_str.find(" at 0x")].split(".")[0].strip()
        implementation_origin = str(implementation_class)[8:-2].split(".")[-1].strip()
        err = f"Unable to build. Procedure `{implementation_origin}.{method_name}()` is not implemented"
        assert method_origin == implementation_origin, err

        # validate implementation: check procedure has the same callable type
        is_implementation_coroutine = inspect.iscoroutinefunction(implementation_method)
        is_origin_coroutine = inspect.iscoroutinefunction(origin_method)
        callable_type = ["def", "async def"]
        iterator_origin = str(origin_class)[8:-2].split(".")[-1].strip()
        err = (
            f"Unable to build. Procedure `{implementation_origin}.{method_name}()` is implemented as `{callable_type[int(is_implementation_coroutine)]}`. "
            f"While the origin `{iterator_origin}.{method_name}()` is defined as `{callable_type[int(is_origin_coroutine)]}`."
        )
        assert is_implementation_coroutine == is_origin_coroutine, err
