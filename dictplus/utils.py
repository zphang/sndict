def replace_none(value, default, lazy=False):
    """Returns a

    Used for better argument resolution

    Parameters
    ----------
    value: object, None
        An object that we intend to replace if None
    default: object, callable
        Either a default returned value or function to be valled if value is None
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
