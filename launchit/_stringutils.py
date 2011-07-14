"""
Converters and definitions for string handling on Python 2 and Python 3.
(Not part of the launchit API)
"""
# Stdlib
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

def convert(obj, out_type):
    """
    Convert `obj` to an instance of `out_type` and return the result. 

    Note that `out_type` must be a string type, otherwise an exception is 
    raised. If `out_type` is an inherited string type, its corresponding
    built-in type is used.
    """
    if issubclass(out_type, altstring):
        return to_alternate_string(obj)
    elif issubclass(out_type, str):
        return to_native_string(obj)
    else:
        raise TypeError('out_type must be a string type')

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
