import tornado.web
import logging
import mimetypes

try:
    from urllib.parse import unquote
    from urllib.parse import urlparse
except ImportError:
    from urllib import unquote
    from urlparse import urlparse

import sys
import os

rootpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, rootpath)
from lib.tracemore import get_exc_plus
from lib.tool import format_size
sys.path.pop(0)
del rootpath


logger = logging.getLogger('filenado.base')

class BaseHandler(tornado.web.RequestHandler):

    def _cache_get_act_idx_sub(func):
        # this will only cache in this instance
        def get_act_idx_sub_wrapper(self, uri=None):
            uri = uri or self.request.uri
            if getattr(self, '_uri', None) != uri:
                self._act_idx_sub = func(self, uri)
                self._uri = uri
            return self._act_idx_sub

        return get_act_idx_sub_wrapper

    @_cache_get_act_idx_sub
    def get_act_idx_sub(self, uri=None):
        # uri must starts with '/'
        # split /home/0/sub/folder to home, 0, sub/folder
        # /home/0/ to home, 0, ''
        # /home to home, '', ''
        uri = uri or self.request.uri
        result = []
        urlpath = urlparse(uri)[2]
        if urlpath.startswith('/'):
            urlpath = urlpath[1:]
        for each in urlpath.split('/', 2):
            result.append(each)
        fill = 3 - len(result)
        for _ in range(fill):
            result.append('')
        return result

    def get_path(self, uri=None):
        _, idx, sub = self.get_act_idx_sub(uri)
        path = self.application.paths[int(idx)]
        if sub:
            result = os.path.join(path, sub)
            if not os.path.exists(result):
                result = os.path.join(path, unquote(sub)).replace('\\', '/')
        else:
            result = os.path.join(path).replace('\\', '/')
        if result.endswith('/') and result != '/' and os.path.isdir(result):
            return result[:-1]
        return result

    def make_attr(self, path, targetdict, extradict={}):
        icon = self.application.icon
        if os.path.isdir(path):
            targetlist = targetdict.setdefault('folder', [])
            attrs = {'name': os.path.split(path)[-1],
                     'poster': icon['folder']}
        else:
            attrs = {'size': format_size(os.path.getsize(path))}
            mime, _ = mimetypes.guess_type(path)
            poster = None
            if mime is None:
                targetlist = targetdict.setdefault('unknown', [])
                poster = icon['unknown']
            elif mime.startswith('image'):
                targetlist = targetdict.setdefault('image', [])
            elif mime.startswith('audio'):
                targetlist = targetdict.setdefault('audio', [])
            elif mime.startswith('video'):
                targetlist = targetdict.setdefault('video', [])
            else:
                targetlist = targetdict.setdefault('unknown', [])
                poster = icon['unknown']
            if poster:
                attrs['poster'] =  poster
        attrs.update(extradict)
        # logger.debug(attrs)
        targetlist.append(attrs)
        
    def write_error(self, status_code, **kwargs):
        info = get_exc_plus()
        logging.error('%s\n%s', status_code, info)
        # uncomment this line for py2
        # return self.__class__.write_error(self, status_code, **kwargs)
        # uncomment this line for py3
        # return super().write_error(status_code, **kwargs)
        # if status_code == 404:
        #     return self.render('404.html')
        self.render('error.html', info=info, code=status_code)


if __name__ == '__main__':
    pass
