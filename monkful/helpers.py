def json_type(var):
    """
    Returns the JSON type for the given `var` where `var` is a variable or
    a `type` instance.

    The return value will be one of the following:

        Number
        String
        Boolean
        Array
        Object
        null
        unknown

    """

    if type(var) is not type:
        var = type(var)

    if var in(unicode, str):
        return 'String'
    elif var in(int, long, float):
        return 'Number'
    elif var is bool:
        return 'Boolean'
    elif var is list:
        return 'Array'
    elif var is dict:
        return 'Object'
    elif var is None:
        return 'null'
    else:
        return 'unknown'
