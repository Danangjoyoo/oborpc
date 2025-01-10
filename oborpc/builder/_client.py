"""
Client RPC Builder
"""
import inspect
import logging
import time
from typing import Any, Callable, Dict, Optional, Union

import httpx
import pydantic_core
from pydantic import BaseModel, create_model

from ..security import BASIC_AUTH_TOKEN
from ..exception import OBORPCBuildException, RPCCallException

# httpx log level
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)


class ClientBuilder:
    """
    Client Builder
    """
    __registered_base = set()

    def __init__(
        self,
        host: str,
        port: Optional[Union[str, int]] = None,
        timeout: Optional[float] = None,
        retry: Optional[int] = None,
        additional_headers: Optional[Dict[str, str]] = None
    ): # pylint: disable=too-many-arguments,too-many-positional-arguments
        self.master_instances = []
        self.host = host
        self.port = port
        self.timeout = timeout or 1
        self.retry = retry or 0

        protocol = "http://"
        if self.check_has_protocol(host):
            protocol = ""

        self.base_url = f"{protocol}{host}"
        if port:
            self.base_url += f":{port}"

        # request client
        headers = {
            "Authorization": f"Basic {BASIC_AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        if additional_headers:
            headers.update(additional_headers)

        self.request_client = httpx.Client(
            base_url=self.base_url,
            headers=headers
        )
        self.async_request_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers
        )

        # model map
        self.model_maps = {}

    def check_has_protocol(self, host: str):
        """
        Check whether the given host already defined with protocol or not
        """
        if host.startswith("http://"):
            return True
        if host.startswith("https://"):
            return True
        return False

    def check_registered_base(self, base: str):
        """
        Check whether the base RPC class is already built
        """
        if base in ClientBuilder.__registered_base:
            msg = f"Failed to build client RPC {base} : base class can only built once"
            raise OBORPCBuildException(msg)
        ClientBuilder.__registered_base.add(base)

    def create_remote_caller(
        self,
        class_name: str,
        method_name: str,
        url_prefix: str,
        timeout: float = None,
        retry: int = None
    ): # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        create remote caller
        """
        def remote_call(*args, **kwargs):
            """
            remote call wrapper
            """
            start_time = time.time()
            try:
                url = f"{url_prefix}/{class_name}/{method_name}"
                response = self.request_client.post(
                    url=url,
                    json=pydantic_core.to_jsonable_python({
                        "args": args[1:],
                        "kwargs": kwargs
                    }),
                    timeout=timeout if timeout is not None else self.timeout
                )

                if not response:
                    msg = f"rpc call failed method={method_name}"
                    raise RPCCallException(msg)

                data = response.json().get("data")
                return self.convert_model_response(class_name, method_name, data)

            except Exception as e:
                _retry = retry if retry is not None else self.retry
                if _retry:
                    return remote_call(*args, **kwargs, retry=_retry-1)

                if isinstance(e, RPCCallException):
                    raise e
                msg = f"rpc call failed method={method_name} : {e}"
                raise RPCCallException(msg) from e

            finally:
                elapsed = f"{(time.time() - start_time) * 1000}:.2f"
                logging.debug("[RPC-Clientt] remote call take %s ms", elapsed)

        return remote_call

    def create_async_remote_caller(
        self,
        class_name: str,
        method_name: str,
        url_prefix: str,
        timeout: float = None,
        retry: int = None
    ): # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        create async remote caller
        """
        async def async_remote_call(*args, **kwargs):
            """
            async remote call wrapper
            """
            start_time = time.time()
            try:
                data = pydantic_core.to_jsonable_python({"args": args[1:], "kwargs": kwargs})
                url = f"{url_prefix}/{class_name}/{method_name}"
                response = await self.async_request_client.post(
                    url=url,
                    json=data,
                    timeout=timeout if timeout is not None else self.timeout
                )

                if not response:
                    msg = f"rpc call failed method={method_name}"
                    raise RPCCallException(msg)

                data = response.json().get("data")
                return self.convert_model_response(class_name, method_name, data)

            except Exception as e:
                _retry = retry if retry is not None else self.retry
                if _retry:
                    return await async_remote_call(*args, **kwargs, retry=_retry-1)

                if isinstance(e, RPCCallException):
                    raise e
                msg = f"rpc call failed method={method_name} : {e}"
                raise RPCCallException(msg) from e

            finally:
                elapsed = f"{(time.time() - start_time) * 1000}:.2f"
                logging.debug("[RPC-Clientt] remote call take %s ms", elapsed)

        return async_remote_call

    def build_client_rpc(self, instance: object, url_prefix: str = ""):
        """
        Setup client rpc
        """
        _class = instance.__class__
        iterator_class = _class

        self.check_registered_base(_class)

        for (name, method) in inspect.getmembers(iterator_class, predicate=inspect.isfunction):
            if name not in iterator_class.__oborprocedures__:
                continue
            class_name = _class.__name__
            self.extract_models(class_name, name, method)
            setattr(_class, name, self.create_remote_caller(class_name, name, url_prefix))

    def build_async_client_rpc(self, instance: object, url_prefix: str = ""):
        """
        Setup async client rpc
        """
        _class = instance.__class__
        iterator_class = _class

        self.check_registered_base(_class)

        for (name, method) in inspect.getmembers(iterator_class, predicate=inspect.isfunction):
            if name not in iterator_class.__oborprocedures__:
                continue
            class_name = _class.__name__
            self.extract_models(class_name, name, method)
            setattr(_class, name, self.create_async_remote_caller(class_name, name, url_prefix))

    def extract_models(
        self,
        class_name: str,
        method_name: str,
        method: Callable
    ):
        """
        Extract pydantic model
        """
        if not class_name in self.model_maps:
            self.model_maps[class_name] = {}

        signature_params = inspect.signature(method).parameters
        params = {
            k: (
                v.annotation if v.annotation != inspect._empty else Any,
                v.default if v.default != inspect._empty else ...
            ) for k, v in signature_params.items()
        }

        signature_return = inspect.signature(method).return_annotation
        self.model_maps[class_name][method_name] = [
            create_model(f"{class_name}_{method_name}", **params),
            signature_return
        ]

    def convert_model_response(
        self,
        class_name: str,
        method_name: str,
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert Pydantic Model Response
        """
        model, return_annotation = self.model_maps[class_name][method_name]
        try:
            if BaseModel.__subclasscheck__(return_annotation.__class__):
                return model.model_validate(response)
        except:
            pass
        return response
