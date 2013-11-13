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
    """
    Creates and returns a dictionary with nested layers and assign
    `value` to the last layer.

    For example:

        create_deep_dict('hello', ['blog', 'post', 'text'])

    Will return:

        { 'blog' { 'post': { 'text': 'hello' } } }
    """

    orig_data = {}
    data = orig_data
    last_layer = layers[-1]

    for layer in layers[:-1]:
        data[layer] = {}
        data = data[layer]

    data[last_layer] = value

    return orig_data

def deep_dict_value(data, layers):
    """
    Returns the value from a dictionary at a certain nested layer.

    For example:

        data = { 'blog' { 'post': { 'text': 'hello' } } }
        deep_dict_value(data, ['blog', 'post', 'text'])

    Will return:

        'hello'
    """

    for layer in layers:
        data = data[layer]

    return data
