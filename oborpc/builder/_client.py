"""
Client RPC Builder
"""
import inspect
import json
import logging
import time
import requests
from ._base import OBORBuilder
from ..exception import RPCCallException


class ClientBuilder(OBORBuilder):
    """
    Client Builder
    """
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
                url = f"{self.base_url}{url_prefix}/{class_name}/{method_name}"
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
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
