"""
Meta File
"""

class OBORMeta(type):
    """
    Meta class used
    """
    __obor_registry__ = {}
    def __new__(mcs, name, bases, namespace, /, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        cls.__oborprocedures__ = {
            methodname for methodname, value in namespace.items()
            if getattr(value, "__isoborprocedure__", False)
        }
        OBORMeta.__obor_registry__[cls] = cls.__oborprocedures__

        return cls


class OBORBase(metaclass=OBORMeta): # pylint: disable=too-few-public-methods
    """
    Obor Base Class
    """
    def __repr__(self) -> str:
        return "<OBORBase(metaclass=OBORMeta)>"

    def __str__(self) -> str:
        return self.__repr__()
