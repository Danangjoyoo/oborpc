"""
"""
import inspect
import json
import requests
import time
from ._base import OBORBuilder


class ClientBuilder(OBORBuilder):
    def __init__(self, host, port=None, timeout=1, retry=0) -> None:
        super().__init__(host, port, timeout, retry)

    def create_remote_caller(self, class_name, method_name, url_prefix, timeout = None, retry = None):
        def remote_call(*args, **kwargs):
            try:
                t0 = time.time()
                data = {
                    "args": args[1:],
                    "kwargs": kwargs
                }
                url = f"{self.base_url}{url_prefix}/{class_name}/{method_name}"
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=json.dumps(data),
                    timeout=timeout if timeout != None else self.timeout
                )
                if not response:
                    raise Exception(f"rpc call failed method={method_name}")
                return response.json().get("data")
            except Exception as e:
                _retry = retry if retry != None else self.retry
                if _retry:
                    return remote_call(*args, **kwargs, retry=_retry-1)
                raise Exception(f"rpc call failed method={method_name}")
            finally:
                # print("elapsed", time.time() - t0)
                pass
        return remote_call

    def setup_client_rpc(self, instance: object, url_prefix: str = ""):
        _class = instance.__class__
        iterator_class = _class

        self.check_registered_base(_class)

        for (name, method) in inspect.getmembers(iterator_class, predicate=inspect.isfunction):
            if name not in iterator_class.__oborprocedures__:
                continue
            setattr(_class, name, self.create_remote_caller(_class.__name__, name, url_prefix))
