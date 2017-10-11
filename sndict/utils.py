import collections as col
import os
import re
import six


# ==== Property Classes ==== #

class GetSetFunctionClass(object):

    def __init__(self, get_func, set_func):
        """Class that provides __getitem__ / __setitem__ methods

        Parameters
        ----------
        get_func: function
            __getitem__ method
        set_func: function
            __setitem__ method
        """
        self._get_func = get_func
        self._set_func = set_func

    def __getitem__(self, key):
        return self._get_func(key)

    def __setitem__(self, key, value):
        self._set_func(key, value)


class GetSetAmbiguousTupleFunctionClass(object):
    def __init__(self, get_func, set_func):
        """Class that provides __getitem__ / __setitem__ methods.
        Because it's ambiguous as to whether a provided key is a tuple or
        multiple arguments, this class assume that tuples/lists are
        multiple arguments.

        Parameters
        ----------
        get_func: function
            __getitem__ method
        set_func: function
            __setitem__ method
        """
        self._get_func = get_func
        self._set_func = set_func

    def __getitem__(self, key):
        if isinstance(key, (tuple, list)):
            return self._get_func(key)
        else:
            return self._get_func((key, ))

    def __setitem__(self, key, value):
        if isinstance(key, (tuple, list)):
            return self._set_func(key, value)
        else:
            return self._set_func((key, ), value)


# ==== Lists ==== #

def list_add(lists_of_lists):
    """Element-wise sum of list of lists

    Parameters
    ----------
    lists_of_lists: list
        List of numbers

    Returns
    -------
    list
    """
    assert len(lists_of_lists) > 0
    new_ls = [0] * len(lists_of_lists[0])
    for sublist in lists_of_lists:
        for i, elem in enumerate(sublist):
            new_ls[i] += elem
    return new_ls


def list_equal(list_a, list_b):
    """Check if two lists are equal

    Parameters
    ----------
    list_a: list
    list_b: list

    Returns
    -------
    bool
    """
    return tuple(list_a) == tuple(list_b)


def list_index(ls, indices):
    """numpy-style creation of new list based on a list of elements and another
    list of indices

    Parameters
    ----------
    ls: list
        List of elements
    indices: list
        List of indices

    Returns
    -------
    list
    """
    return [ls[i] for i in indices]


def list_is_unique(ls):
    """Check if every element in a list is unique

    Parameters
    ----------
    ls: list

    Returns
    -------
    bool
    """
    return len(ls) == len(set(ls))


# ==== Tuples ==== #

def tuple_constructor(*args):
    """Construct tuple from *args syntax

    Parameters
    ----------
    args: list
        Arguments

    Returns
    -------
    tuple
    """
    return tuple(args)


# ==== Dicts ==== #

def dict_to_string(dictionary, indent=4):
    """Serialize dict as string

    Parameters
    ----------
    dictionary: dict
    indent: int
        Number of spaces to indent per level

    Returns
    -------
    str
    """
    if len(dictionary) == 0:
        return "{}"
    indentation = " " * indent
    string = "{\n"
    for key, val in six.iteritems(dictionary):
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


def list_to_dict(ls, key_func=None, val_func=None):
    assert (key_func is not None) != (val_func is None)
    new_dict = col.OrderedDict()

    if key_func:
        for elem in ls:
            new_dict[key_func(elem)] = elem
    else:
        for elem in ls:
            new_dict[elem] = val_func(elem)

    assert len(new_dict) == len(ls),\
        "Keys are not unique"
    return new_dict


# ==== Strings ==== #

def strip_spaces(string):
    """Remove white-space from a string
    Parameters
    ----------
    string: str

    Returns
    -------
    str
    """
    pattern = re.compile(r'\s+')
    return re.sub(pattern, '', string)


def get_str_func(mode):
    """Choose method to string-serialize an object

    Parameters
    ----------
    mode: "type", "str" or "repr"
        How to serialize terminal value

    Returns
    -------
    function
    """
    if mode == "type":
        return type
    elif mode == "str":
        return str
    elif mode == "repr":
        return repr
    else:
        raise KeyError("Unknown serialization mode")


# ==== Functions ==== #

def replace_none(value, default, lazy=False):
    """Return value if it's not None, otherwise return default value

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


def negate(func):
    """Returns a function that returns 'not' of input functions

    Parameters
    ----------
    func: function

    Returns
    -------
    function
    """
    def negated_func(*args, **kwargs):
        return not func(*args, **kwargs)
    return negated_func


# ==== System ==== #

def split_path(path):
    """Split a path into tokens

    Parameters
    ----------
    path: str
        A system path

    Returns
    -------
    list
    """
    return os.path.normpath(path).split(os.sep)
