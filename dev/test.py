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
        if type(layer) == list:
            for item in data:
                if item[layer[0]] == layer[1]:
                    data = item
                    break
        else:
            data = data[layer]

    return data

print deep_dict_value(
    {u'5283b1e2aa2649a692a03415': {u'comments': [{'wajooo': 'hoho', 'id': '52860473aa26496626ea3f5d'}]}},
    [u'5283b1e2aa2649a692a03415', u'comments', ['id', '52860473aa26496626ea3f5d']]
)

"""

orig = [u'5283b1e2aa2649a692a03415', u'comments', u'52860473aa26496626ea3f5d']

second = [u'5283b1e2aa2649a692a03415', u'comments', ['id', '52860473aa26496626ea3f5d']]


{
    'comments': [
        {
            'id': '52860473aa26496626ea3f5d'
        }
    ]
}

"""
