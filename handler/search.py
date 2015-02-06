import tornado.web
import fnmatch
import re
import logging
import mimetypes

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from handler.base import BaseHandler
from lib.tool import format_size
sys.path.pop(0)

windows = sys.platform.startswith('win')
logger = logging.getLogger('filenado.search')


class SearchHandler(BaseHandler):

    def get(self, rule):
        rule, idx, sub = self.get_act_idx_sub()
        
        if idx:
            home = False
            folder = self.get_path()
        else:
            home = True

        pattern = self.get_argument('pattern', None)
        if pattern is None:
            return self.render_file(pattern='')

        limit = self.get_argument('limit')
        if not limit:
            limit = '0'
        if not limit.isdigit():
            return self.render_file(pattern=pattern, info='depth "%s" is not a number'%limit)

        limit = int(limit)
        if limit == 0:
            limit = float('inf')

        if rule == 're':
            default = self.get_argument('sensitivity', 'insensitive')
            result = self.re(pattern, limit, default, idx)
            if result is None:
                return
        else:
            if windows:
                default = 'insensitive'
            else:
                default = self.get_argument('sensitivity', 'insensitive')
            result = self.fn(pattern, limit, default, idx)
        if limit == float('inf'):
            limit = 0
        return self.render_file(result=result, pattern=pattern, limit=limit, default=default)

    def render_file(self, **kwd):
        therule, theidx, sub = self.get_act_idx_sub()
        rule = kwd.get('rule', therule)
        idx = kwd.get('idx', theidx)
        limit = kwd.get('limit', 0)
        pattern = kwd.get('pattern', None)
        result = kwd.get('result', None)
        if not pattern:
            if rule == 're':
                pattern = '.*'
            else:
                pattern = '*'

        info = kwd.get('info', '')

        default = kwd.get('default', 'insensitive')

        if rule == 're':
            toname = 'Unix-Shell'
            to = 'fn'
        else:
            toname = 'Regular'
            to = 're'
        
        if not idx:
            sublink = ''
        elif not sub:
            sublink = idx
        else:
            sublink = '/'.join((idx, sub))

        switchlink = "/%s/%s"%(to, sublink)

        if not idx:
            folder = ('home', '/home/')
        else:
            path = self.get_path()
            dirname, name = os.path.split(path)
            if not name:
                name = dirname
            # if os.path.isfile(path):
            #     link = '/home/%s'%sublink
            # else:
            #     link = '/home/%s/'%sublink
            
            link = '/home/%s'%sublink
            folder = (name, link)

        return self.render('search.html', rule=rule, toname=toname, 
                           switch_link=switchlink, folder=folder,
                           default=default, limit=limit, pattern=pattern,
                           result=result, windows=windows, info=info)

    def walk(self, path=None):
        path_collect = []

        # search a folder
        if path is not None:
            if path.endswith('/') and path != '/':
                path = path[:-1]

            if os.path.isfile(path):
                # yield (os.path.dirname(path), [], [path])
                raise StopIteration()
            path_collect.append(path)

        # search home, deal the first walk
        else:
            files = []
            folders = []
            for each in self.application.paths:
                if os.path.isdir(each):
                    folders.append(each)
                else:
                    files.append(each)
            yield ('', folders, files)
            path_collect.extend(folders)

        while path_collect:
            path = path_collect.pop(0)
            path, folders, files = next(os.walk(path))
            yield (path, folders, files)
            for folder in folders:
                path_collect.append(os.path.join(path, folder).replace('\\', '/'))

    def pathjoin(self, home, *subs):
        if not home:
            return os.path.join(*subs).replace('\\', '/')
        return os.path.join(home, *subs).replace('\\', '/')

    def makelink(self, path):
        # only treat path as file
        # you should ensure replace '\\' to '/'
        for idx, eachpath in enumerate(self.application.paths):
            if path.startswith(eachpath):
                relativepath = os.path.relpath(path, eachpath)
                if relativepath == '.':
                    return '/home/%s'%idx
                return '/home/%s/%s'%(idx, relativepath)
        else:
            logger.critical('%s filed to make link', path)
            raise tornado.HTTPError(500, '%s filed to make link'%path)
   
    def get_depth(self, path, target=None):#, offset=0):
        if not path:
            return 0

        assert os.path.isdir(path), '%s is not a path'%path
        if not target:
            targets = self.application.paths
        else:
            targets = [target]
        
        for each in targets:
            if path.startswith(each):
                relativepath = os.path.relpath(path, each)
                if relativepath == '.':
                    return 0#+offset
                return relativepath.count('/')+1#+offset

        raise AttributeError('fixme: failed to get depth for %s in %s'%(path, targets))

    def _cache_search(func=None, cleancache=False):
        cache = {}

        def wrapped_fn(self, *args):
            funcname = getattr(func, 'func_name', getattr(func, '__name__', ''))
            if (args not in cache.setdefault(funcname, {}) 
                    or self.get_argument('nocache', False)):
                cache[funcname][args] = func(self, *args)
                logger.debug('get freash')
            else:
                logger.debug('get from cache')
            return cache[funcname][args]

        return wrapped_fn

    @_cache_search
    def fn(self, pattern, limit, style, idx):
        if not pattern:
            return []
        
        if style == 'sensitive':
            match = lambda x: fnmatch.fnmatchcase(x, pattern)
        else:
            match = lambda x: fnmatch.fnmatch(x, pattern)
        return self._search(match, limit, idx)

    @_cache_search
    def re(self, pattern, limit, style, idx):
        if not pattern:
            return []
        if style == "sensitive":
            flags = 0
        else:
            flags = re.I
        try:
            p = re.compile(pattern, flags=flags)
        except BaseException as e:
            return self.render_file(info="invalid pattern %s - %s"%(pattern, e))
        return self._search(p.search, limit, idx)

    def _search(self, func, limit, idx):
        result = {}
        if not idx:
            target = None
            walker = self.walk()
        else:
            target = self.get_path()
            walker = self.walk(target)

        for path, folders, files in walker:
            depth = self.get_depth(path, target)#, int(not idx))
            if depth >= limit:
                logger.info('%s hit the depth', path)
                break
            for each in filter(func, files):
                filepath = self.pathjoin(path, each)
                link = self.makelink(filepath)
                self.make_attr(filepath, result, {'link': link, 'name': each})

        return result