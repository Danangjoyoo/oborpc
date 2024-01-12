"""
"""

class OBORBuilder():
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
        if host.startswith("http://"):
            return True
        if host.startswith("https://"):
            return True
        return False

    def check_registered_base(self, base: str):
        if base in OBORBuilder.__registered_base:
            raise Exception(f"Failed to build client RPC {base} : base class can only built once")
        OBORBuilder.__registered_base.add(base)
