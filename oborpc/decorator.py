"""
"""
import inspect

def procedure(fun):
    if not inspect.isfunction(fun):
        raise TypeError("can only applied for function or method")
    fun.__isoborprocedure__ = True
    return fun
