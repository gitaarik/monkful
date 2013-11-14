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

        if layer is list:
            data = []
            data.append({})
            data = data[0]
        else:
            data[layer] = {}
            data = data[layer]

    data[last_layer] = value

    return orig_data

print create_deep_dict('jo', ['one', 'two', list, 'three', 'four'])

"""

{
    'one': {
        'two' [
            {
                'three': {
                    'four': {
                    }
                }
            }
        ]
    }
}

"""
