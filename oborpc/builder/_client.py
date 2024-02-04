"""
Client RPC Builder
"""
import inspect
import json
import logging
import time
import httpx
from ..security import BASIC_AUTH_TOKEN
from ..exception import OBORPCBuildException, RPCCallException


class ClientBuilder:
    """
    Client Builder
    """
    __registered_base = set()

    def __init__(self, host, port=None, timeout=1, retry=0) -> None:
        self.master_instances = []
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retry = retry

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
        self.request_client = httpx.Client(
            base_url=self.base_url,
            headers=headers
        )
        self.async_request_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers
        )

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
    ): # pylint: disable=too-many-arguments
        """
        create remote caller
        """
        def remote_call(*args, **kwargs):
            """
            remote call wrapper
            """
            start_time = time.time()
            try:
                data = {
                    "args": args[1:],
                    "kwargs": kwargs
                }
                url = f"{url_prefix}/{class_name}/{method_name}"
                response = self.request_client.post(
                    url=url,
                    json=json.dumps(data),
                    timeout=timeout if timeout is not None else self.timeout
                )

                if not response:
                    msg = f"rpc call failed method={method_name}"
                    raise RPCCallException(msg)

                return response.json().get("data")

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
    ): # pylint: disable=too-many-arguments
        """
        create async remote caller
        """
        async def async_remote_call(*args, **kwargs):
            """
            async remote call wrapper
            """
            start_time = time.time()
            try:
                data = {
                    "args": args[1:],
                    "kwargs": kwargs
                }
                url = f"{url_prefix}/{class_name}/{method_name}"
                response = await self.async_request_client.post(
                    url=url,
                    json=json.dumps(data),
                    timeout=timeout if timeout is not None else self.timeout
                )

                if not response:
                    msg = f"rpc call failed method={method_name}"
                    raise RPCCallException(msg)

                return response.json().get("data")

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

        for (name, _) in inspect.getmembers(iterator_class, predicate=inspect.isfunction):
            if name not in iterator_class.__oborprocedures__:
                continue
            setattr(_class, name, self.create_remote_caller(_class.__name__, name, url_prefix))

    def build_async_client_rpc(self, instance: object, url_prefix: str = ""):
        """
        Setup async client rpc
        """
        _class = instance.__class__
        iterator_class = _class

        self.check_registered_base(_class)

        for (name, _) in inspect.getmembers(iterator_class, predicate=inspect.isfunction):
            if name not in iterator_class.__oborprocedures__:
                continue
            setattr(_class, name, self.create_async_remote_caller(_class.__name__, name, url_prefix))
