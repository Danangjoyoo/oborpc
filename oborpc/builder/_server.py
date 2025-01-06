"""
Server Builder Base
"""
import inspect
import pydantic_core
from pydantic import BaseModel, create_model
from typing import Any

class ServerBuilder:
    """
    Server Builder
    """
    def __init__(self) -> None:
        self.model_maps = {}

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

    def dispatch_rpc_request(self, class_name, method_name, instance, method, body):
        """
        Dispatch RPC Request
        """
        kwargs = self.construct_model_object(class_name, method_name, body)
        res = method(instance, **kwargs)
        return {"data": self.convert_model_response(res)}

    async def dispatch_rpc_request_async(self, class_name, method_name, instance, method, body):
        """
        Dispatch RPC Request
        """
        kwargs = self.construct_model_object(class_name, method_name, body)
        res = await method(instance, **kwargs)
        return {"data": self.convert_model_response(res)}

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
            class_name = iterator_class.__name__
            self.extract_models(class_name, name, method)
            if inspect.iscoroutinefunction(method):
                self.create_remote_responder_async(instance, router, class_name, name, method)
            else:
                self.create_remote_responder(instance, router, class_name, name, method)

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

    def extract_models(self, class_name, method_name, method):
        """
        """
        if not class_name in self.model_maps:
            self.model_maps[class_name] = {}

        signature_params = inspect.signature(method).parameters
        params = {
            k: (
                v.annotation if v.annotation != inspect._empty else Any,
                v.default if v.default != inspect._empty else ...
            ) for i, (k, v) in enumerate(signature_params.items())
            if i != 0
        }

        self.model_maps[class_name][method_name] = [
            list(signature_params.keys())[1:],
            create_model(f"{class_name}_{method_name}", **params)
        ]

    def construct_model_object(self, class_name, method_name, body):
        """
        """
        arg_keys, model = self.model_maps[class_name][method_name]
        args = body.get("args", [])
        kwargs = body.get("kwargs", {})
        for i, arg in enumerate(args):
            kwargs[arg_keys[i]] = arg
        return vars(model.model_validate(kwargs))

    def convert_model_response(self, response):
        """
        """
        if BaseModel.__subclasscheck__(response.__class__):
            return response.model_dump()
        return response
