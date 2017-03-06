def replace_none(value, default, lazy=False):
    if value is None:
        if lazy:
            return default()
        else:
            return default
    else:
        return value
