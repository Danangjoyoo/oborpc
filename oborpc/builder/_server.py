"""
Server Builder Base
"""
import inspect
from typing import Any, Callable, Dict, List

from pydantic import BaseModel, create_model

class ServerBuilder:
    """
    Server Builder
    """
    def __init__(self) -> None:
        self.model_maps: Dict[str, Dict[str, Any]] = {}

    def create_remote_responder(self, instance, router, class_name, method_name, method): # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Remote RPC Request Responder
        """
        raise NotImplementedError("method should be overridden")

    def create_remote_responder_async(self, instance, router, class_name, method_name, method): # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Remote RPC Request Responder Async
        """
        raise NotImplementedError("method should be overridden")

    def dispatch_rpc_request(self, class_name, method_name, instance, method, body): # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Dispatch RPC Request
        """
        kwargs = self.construct_model_object(class_name, method_name, body)
        res = method(instance, **kwargs)
        return {"data": self.convert_model_response(res)}

    async def dispatch_rpc_request_async(self, class_name, method_name, instance, method, body): # pylint: disable=too-many-arguments,too-many-positional-arguments
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
                self.validate_implementation(
                    name,
                    method,
                    _class,
                    iterator_method,
                    iterator_class
                )

            # build router
            class_name = iterator_class.__name__
            self.extract_models(class_name, name, method)
            if inspect.iscoroutinefunction(method):
                self.create_remote_responder_async(instance, router, class_name, name, method)
            else:
                self.create_remote_responder(instance, router, class_name, name, method)

    def validate_implementation(
        self,
        method_name: str,
        implementation_method: Callable,
        implementation_class: object,
        origin_method: Callable,
        origin_class: object,
    ): # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Validate implementation of RPC super class
        """
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
            f"Unable to build. Procedure `{implementation_origin}.{method_name}()` "
            f"is implemented as `{callable_type[int(is_implementation_coroutine)]}`. "
            f"While the origin `{iterator_origin}.{method_name}()` is defined as "
            f"`{callable_type[int(is_origin_coroutine)]}`."
        )
        assert is_implementation_coroutine == is_origin_coroutine, err

    def extract_models(self, class_name: str, method_name: str, method: Callable):
        """
        Extract pydantic models from method signature for both spec and returns
        """
        if not class_name in self.model_maps:
            self.model_maps[class_name] = {}

        signature = inspect.signature(method)

        # request signature
        request_params = {
            k: (
                v.annotation if v.annotation != inspect._empty else Any,
                v.default if v.default != inspect._empty else ...
            ) for i, (k, v) in enumerate(signature.parameters.items())
            if i != 0
        }
        kwargs_model = create_model(f"{class_name}_{method_name}_request_kwargs", **request_params)
        request_premodel = {
            "args": (List[Any], []),
            "kwargs": (kwargs_model, ...)
        }
        request_model = create_model(f"{class_name}_{method_name}_request", **request_premodel)

        # response signature
        return_annot = signature.return_annotation
        return_annot = return_annot if return_annot != inspect._empty else Any
        response_params = {"data": (return_annot, ...)}

        self.model_maps[class_name][method_name] = [
            list(signature.parameters.keys())[1:],
            kwargs_model,
            request_model,
            create_model(f"{class_name}_{method_name}_reponse", **response_params)
        ]

    def construct_model_object(
        self,
        class_name: str,
        method_name: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Construct pydantic object with the declared model and the given request body
        """
        arg_keys, kwargs_model, _, _ = self.model_maps[class_name][method_name]
        args = body.get("args", [])
        kwargs = body.get("kwargs", {})
        for i, arg in enumerate(args):
            kwargs[arg_keys[i]] = arg
        return vars(kwargs_model.model_validate(kwargs))

    def convert_model_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert response into pydantic model if possible
        """
        if BaseModel.__subclasscheck__(response.__class__):
            return response.model_dump()
        return response
