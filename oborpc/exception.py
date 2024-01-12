"""
OBORPC Exceptions
"""

class OBORPCBuildException(Exception):
    """
    Build Related Exceptions
    """
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class RPCCallException(Exception):
    """
    Any Exception during RPC Call
    """
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
