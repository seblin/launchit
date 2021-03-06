"""
Abstractions to convert between native and alternate strings on Python 2 and 
Python 3. (Not part of the launchit API)
"""
# Stdlib
import functools
import sys

# Launchit package
from . import settings

on_py3k = sys.version_info >= (3,0)

# Encoding used when unicode/bytes must be converted to strings and vice versa
ENCODING = settings.config['encoding']

# The Python version's "alternate" string type
altstring = bytes if on_py3k else unicode

# Abstract "type" for alternate and native strings (disappeared with Python 3)
basestring = (str, altstring)

def keep_string_type(wrapped_func):
    """
    A decorator, which guarantees, that the value returned by the wrapped
    function will have the same string-type as the wrapped function's first 
    argument has. If `wrapped_func` has no arguments or if the result is not
    a string-type, then the original result of `wrapped_func` is returned.
    """
    @functools.wraps(wrapped_func)
    def wrapper(*args, **kwargs):
        result = wrapped_func(*args, **kwargs)
        if args and isinstance(result, basestring):
            result = convert(result, type(args[0]))
        return result
    return wrapper

def convert(obj, out_type):
    """
    Convert `obj` to an instance of `out_type`, where `out_type` must be a
    string type and return the result. If `out_type` is not a string type, 
    a `TypeError` is raised.
    """
    if issubclass(out_type, altstring):
        result = to_alternate_string(obj)
    elif issubclass(out_type, str):
        result = to_native_string(obj)
    else:
        raise TypeError('Cannot convert to non-string type')
    return out_type(result)

def to_alternate_string(obj):
    """
    Convert given object to an alternate string. 

    If `obj` is already an alternate string, it is returned unchanged. 
    Otherwise `str()` is called on the object and the result is then 
    encoded/decoded to its alternate string version.
    """
    if isinstance(obj, altstring):
        return obj
    return str(obj).encode(ENCODING) if on_py3k else str(obj).decode(ENCODING)

def to_native_string(obj):
    """
    Convert given object to a native string.

    If `obj` is an alternate string, it is encoded/decoded to its native 
    string version. Otherwise `str()` is called on the object and that 
    result is returned.
    """
    if not isinstance(obj, altstring):
        return str(obj)
    return obj.decode(ENCODING) if on_py3k else obj.encode(ENCODING)
