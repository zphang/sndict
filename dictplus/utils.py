import re


class DefaultArgumentClass(object):
    """Non-informative class for expressing "default" values, that isn't None"""
    pass

DEFAULT_ARGUMENT = DefaultArgumentClass()


class GetFunctionClass(object):
    def __init__(self, func):
        self._func = func

    def __getitem__(self, key):
        return self._func(key)


class GetSetFunctionClass(object):
    def __init__(self, get_func, set_func):
        self._get_func = get_func
        self._set_func = set_func

    def __getitem__(self, key):
        return self._get_func(key)

    def __setitem__(self, key, value):
        self._set_func(key, value)


def strip_spaces(string):
    pattern = re.compile(r'\s+')
    return re.sub(pattern, '', string)


def is_default_argument(arg):
    return isinstance(arg, DefaultArgumentClass)


def replace_none(value, default, lazy=False):
    """Returns a

    Used for better argument resolution

    Parameters
    ----------
    value: object, None
        An object that we intend to replace if None
    default: object, callable
        Either a default returned value or function to be called if value is
        None
    lazy: bool, optional
        If True, default is a 0-argument function that is run if value is None.
        If False, default is treated as a value

    Returns
    -------
    object
    """
    if value is None:
        if lazy:
            return default()
        else:
            return default
    else:
        return value


def identity(x):
    """Returns the argument, unmodified.

    Parameters
    ----------
    x: object
        Return the same object

    Returns
    -------
    x: object
    """
    return x


def list_add(lists_of_lists):
    assert len(lists_of_lists) > 0
    new_ls = [0] * len(lists_of_lists[0])
    for sublist in lists_of_lists:
        for i, elem in enumerate(sublist):
            new_ls[i] += elem
    return new_ls


def list_equal(list_a, list_b):
    return tuple(list_a) == tuple(list_b)


def list_index(ls, indices):
    return [ls[i] for i in indices]


def dict_to_string(dictionary, indent=4):
    if len(dictionary) == 0:
        return "{}"
    indentation = " " * indent
    string = "{\n"
    for key, val in dictionary.iteritems():
        if isinstance(val, dict):
            if len(val) == 0:
                string += "{}{}: {{}}".format(indentation, repr(key))
            else:
                string += "{}{}: ".format(indentation, repr(key))
                dict_string_lines = dict_to_string(val).splitlines()
                string += dict_string_lines[0]
                for line in dict_string_lines[1:]:
                    string += "\n{}{}".format(
                        indentation, line
                    )
        else:
            string += "{}{}: {}".format(
                indentation, repr(key), repr(val)
            )
        string += ",\n"
    string += "}"
    return string


def tuple_constructor(*args):
    return tuple(args)


def list_is_unique(ls):
    return len(ls) == len(set(ls))


def negate(func):
    def negated_func(*args, **kwargs):
        return not func(*args, **kwargs)
    return negated_func
