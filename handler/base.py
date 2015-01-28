import tornado.web
import logging

try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote

import sys
import os

rootpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, rootpath)
from lib.tracemore import get_exc_plus
sys.path.pop(0)
del rootpath


logger = logging.getLogger('filenado.base')

class BaseHandler(tornado.web.RequestHandler):

    def write_error(self, status_code, **kwargs):
        logging.error('%s\n%s', status_code, get_exc_plus())
        # uncomment this line for py2
        # return self.__class__.write_error(self, status_code, **kwargs)
        # uncomment this line for py3
        # return super().write_error(status_code, **kwargs)
        # if status_code == 404:
        #     return self.render('404.html')
        self.render('error.html', info=get_exc_plus(), code=status_code)


if __name__ == '__main__':
    pass
