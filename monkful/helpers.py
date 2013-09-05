def json_type(var):
    """
    Returns the JSON type for the given `var` where `var` is a variable or
    a type.

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

    if var == unicode:
        return 'String'
    elif var == int:
        return 'Number'
    elif var == bool:
        return 'Boolean'
    elif var == list:
        return 'Array'
    elif var == dict:
        return 'Object'
    elif var == None:
        return 'null'
    else:
        return 'unknown'
