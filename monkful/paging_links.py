from __future__ import absolute_import, unicode_literals

from copy import copy
from urllib import urlencode


class PagingLinks(object):

    def __init__(self, base_url, default_params):
        self.base_url = base_url
        self.default_params = default_params
        self.links = []

    def add_link(self, rel, page):

        params = copy(self.default_params)
        params.update({'page': page})

        self.links.append({
            'rel': rel,
            'url': '{}?{}'.format(self.base_url, urlencode(params))
        })

    def get_links(self):

        return [
            '<{}>; rel="{}"'.format(
                link['url'],
                link['rel']
            )
            for link in self.links
        ]
