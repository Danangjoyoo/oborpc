"""
Meta File
"""

class OBORPCMeta(type):
    """
    Meta class used to construct RPC
    """
    __obor_registry__ = {}
    def __new__(mcs, name, bases, namespace, /, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        cls.__oborprocedures__ = {
            methodname for methodname, value in namespace.items()
            if getattr(value, "__isoborprocedure__", False)
        }
        OBORPCMeta.__obor_registry__[cls] = cls.__oborprocedures__

        return cls


class RPCBase(metaclass=OBORPCMeta): # pylint: disable=too-few-public-methods
    """
    Obor Base Class
    """
    def __repr__(self) -> str:
        return "<RPCBase(metaclass=OBORPCMeta)>"

    def __str__(self) -> str:
        return self.__repr__()
