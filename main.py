# coding: utf-8
'''
Usage:
main.py [options] [<path>...]

Options:
-r --root=<path>          the folder you want to share. This will shadow `<path>`
-c --config=<config>      the extra details for each file under <path>, if not provide, will try to find `.config.json` file under each `<path>`
-p --port=<port>          listen to this port[default: 8000]
-l --logging=<level>      log level, can be `DEBUG`, `INOF`, `WARNING`, `ERROR`, `CRITICAL`, or number from 0 to 50[default: INFO]
-h --help                 show this message
'''

from __future__ import unicode_literals
import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.log

import logging
import os
import subprocess
import collections

from handler.base import BaseHandler
from handler.exc import UrlFixOr404Handler
from handler.path import HomeHandler
from handler.path import FileHandler
from handler.path import FolderHandler
from handler.search import SearchHandler
from handler.ui import FolderModule
from handler.ui import ImageModule
from handler.ui import VideoModule
from handler.ui import AudioModule
from handler.ui import UnknownModule
from lib.tracemore import get_exc_plus
# from lib.tool import split_endname
from lib.tool import open
from lib.bashlog import getlogger
from lib.bashlog import DEBUG, INFO, WARNING, ERROR, CRITICAL

# remove default tornado logger settings
tornadologger = logging.getLogger('tornado')
for _hdlr in tornadologger.handlers:
    tornadologger.removeHandler(_hdlr)

    for _filter in tornadologger.filters:
        tornadologger.removeFilter(_filter)

logger = logging.getLogger('filenado')


class Application(tornado.web.Application):
    def __init__(self, setting):
        self.ignore = setting.pop('ignore')
        self.icon = setting.pop('icon')
        self.thisdir = setting.pop('thisdir')
        self.paths = setting.pop('paths')
        handlers = [
            (r'^/$', RootHandler),
            # (r'^/cmd/?$', CmdHandler),    # an example

            (r'^/home/$', HomeHandler),

            (r'^/home/\d+/$', FolderHandler),    # shared folders may have same name under different folder 
            (r'^/home/\d+/.+/$', FolderHandler),    # so use number instead of name

            (r'^/home/\d+$', FileHandler),
            (r'^/home/\d+/.+$', FileHandler),

            (r'^/(fn|re)/$', SearchHandler),
            (r'^/(fn|re)/\d+/$', SearchHandler),
            (r'^/(fn|re)/\d+/.+/$', SearchHandler),

            (r'.*', UrlFixOr404Handler),
        ]

        # This may slow down the speed of loading pages
        # Change this for custom
        setting['ui_modules'] = {
            'Folder': FolderModule,
            'Image': ImageModule,
            'Video': VideoModule,
            'Audio': AudioModule,
            'Unknown': UnknownModule}
        setting['template_path'] = os.path.join(self.thisdir, 'template')
        setting['static_path'] = os.path.join(self.thisdir, 'static')
        super(Application, self).__init__(handlers, **setting)

class RootHandler(BaseHandler):
    def get(self):
        details = []
        for idx, path in enumerate(self.application.paths):
            info = {}
            dirname, folder = os.path.split(path)
            info['position'] = dirname
            if folder:
                info['folder'] = folder
            else:
                info['folder'] = dirname
            # if pair[1]:
            #     info['folder'] = pair[1]
            #     info['position'] = pair[0]
            # else:
            #     info['folder'] = pair[0]
            #     info['position'] = None

            if os.path.isfile(path):
                info['explore_link'] = '/home/%s'%idx
            else:
                info['explore_link'] = '/home/%s/'%idx
                info['re_link'] = '/re/%s'%idx
                info['fn_link'] = '/fn/%s'%idx
            details.append(info)

        return self.render('root.html', details=details)



# class CmdHandler(BaseHandler):
#     def get(self):
#         cmd = self.get_argument('cmd', None)
#         if cmd is not None:
#             logger.warning('cmd: %s', cmd)
#             prog = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE)
#             prog.wait(timeout=5)
#             out = prog.stdout.read()
#             err = prog.stderr.read()
#         else:
#             out, err = None, None
#         return self.render('cmd.html', cmd=cmd, out=out, err=err)


def main(port, **setting):
    http_server = tornado.httpserver.HTTPServer(Application(setting), xheaders=True)
    http_server.listen(port)
    logger.info('[port: %s]Sever started.', port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    from docopt import docopt
    import logging
    import json
    import os

    args = docopt(__doc__, help=True)

    level = args['--logging']
    if level.isdigit():
        level = int(level)
    else:
        level = dict(debug=DEBUG, info=INFO, warning=WARNING, critical=CRITICAL)[level.lower()]
    getlogger(logger, level, True)
    getlogger(tornadologger, level, True)

    this_dir = os.path.dirname(__file__)
    with open(os.path.join(this_dir, 'config.json'), 'r', encoding='utf-8') as f:
        setting = json.load(f)
    setting['thisdir'] = this_dir

    if args['--root'] is None:
        root = args['<path>'] or setting['sharepath']
    else:
        root = [args['--root']]


    if root:
        paths = []
        for each in root:
            path = os.path.abspath(os.path.normpath(os.path.expanduser(each))).replace('\\', '/')
            if path != '/' and path.endswith('/'):
                path = path[:-1]
            paths.append(path)
    else:
        paths = [os.path.abspath(os.getcwd()).replace('\\', '/')]

    if not all(map(os.path.exists, paths)):
        raise SystemExit("some path(%s) not found"%paths)

    setting['paths'] = paths

    logger.info('share file %s', setting['paths'])

    main(int(args['--port']), **setting)
