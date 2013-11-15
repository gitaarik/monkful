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

def create_deep_dict(value, layers):

    data = {}
    layer = layers[0]

    if layers[1:]:

        if type(layer) is list:
            data = [create_deep_dict(value, layers[1:])]
            data[0][layer[0]] = layer[1]
        else:
            data[layer] = create_deep_dict(value, layers[1:])

    else:

        if type(layer) is list:
            data = [value]
            data[0][layer[0]] = layer[1]
        else:
            data[layer] = value

    return data

def deep_dict_value(data, layers):

    for layer in layers:
        if type(layer) == list:
            for item in data:
                if item[layer[0]] == layer[1]:
                    data = item
                    break
        else:
            data = data[layer]

    return data
