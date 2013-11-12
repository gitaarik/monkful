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

    if var == unicode or var == str:
        return 'String'
    elif var == int or var == float:
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

def create_deep_dict(layers, value):

    layers = layers[:]
    data = {}
    layer = layers.pop(0)

    if layers:
        data[layer] = create_deep_dict(layers, value)
    else:
        data[layer] = value

    return data

def deep_dict_value(layers, data):

    layers = layers[:]
    layer = layers.pop(0)

    if layers:
        return deep_dict_value(layers, data[layer])
    else:
        return data[layer]
