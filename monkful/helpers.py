def json_type(var):
    """
    Returns the JSON type for the given `var` where `var` is a variable or
    a `type` instance.

    The return value will be one of the following:

        number
        string
        boolean
        array
        object
        null
        unknown

    """

    if type(var) is not type:
        var = type(var)

    if var in(unicode, str):
        return 'string'
    elif var in(int, long, float):
        return 'number'
    elif var is bool:
        return 'boolean'
    elif var is list:
        return 'array'
    elif var is dict:
        return 'object'
    elif var is None:
        return 'null'
    else:
        return 'unknown'
