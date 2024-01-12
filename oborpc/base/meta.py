"""
Meta File
"""

class OBORMeta(type):
    """
    Meta class used
    """
    __obor_registry__ = {}
    def __new__(mcls, name, bases, namespace, /, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)

        cls.__oborprocedures__ = {
            methodname for methodname, value in namespace.items()
            if getattr(value, "__isoborprocedure__", False)
        }
        OBORMeta.__obor_registry__[cls] = cls.__oborprocedures__

        return cls


class OBORBase(metaclass=OBORMeta):
    """
    Obor Base Class
    """
