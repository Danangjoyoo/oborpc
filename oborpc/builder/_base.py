"""
OBORPC Base Builder
"""
from ..exception import OBORPCBuildException

class OBORBuilder():
    """
    OBORPC Builder Class
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
        if base in OBORBuilder.__registered_base:
            msg = f"Failed to build client RPC {base} : base class can only built once"
            raise OBORPCBuildException(msg)
        OBORBuilder.__registered_base.add(base)
