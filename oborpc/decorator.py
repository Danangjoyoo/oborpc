"""
OBORPC Decorator
"""
import inspect
from typing import Any, Callable, TypeVar

DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])

def procedure(fun: Callable) -> DecoratedCallable:
    """
    Marks the method with this decorator to make it available
    for RPC within the class with direct inheritance with `RPCBase`.
    To make it works also make sure the method is overridden
    in the server class inheritance of the base class

    from oborpc.base import meta
    from oborpc.decorator import procedure

    class Calculator(meta.RPCBase):
        @procedure
        def add(self, a, b):
            pass

    class CalculatorServer(Calculator):
        def tambah(self, a, b):
            return a + b
    """
    if not inspect.isfunction(fun):
        raise TypeError("can only applied for function or method")
    fun.__isoborprocedure__ = True
    return fun
