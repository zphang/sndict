import types

from .utils import negate


def get_filter_func(criteria, filter_out=False):
    """Create filter function from criteria, based on type"""
    if criteria == slice(None):
        filter_func = lambda x: True
    elif isinstance(criteria, types.FunctionType):
        filter_func = criteria
    elif isinstance(criteria, (list, set)):
        filter_func = lambda x: x in criteria
    else:
        filter_func = lambda x: x == criteria

    if filter_out:
        filter_func = negate(filter_func)

    return filter_func
