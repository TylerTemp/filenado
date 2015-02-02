import tornado.web
import tornado.httputil
import tornado.gen
import tornado.iostream
import logging
import mimetypes
import fnmatch

try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from handler.base import BaseHandler
from lib.tool import size
sys.path.pop(0)

logger = logging.getLogger('filenado.path')

class _Handler(BaseHandler):
    def _get_path(self, idx, sub=None):
        if not idx.isdigit():
            logger.debug('idx %s must be digit', idx)
            raise tornado.web.HTTPError(404)
        idx = int(idx)
        pathfolder = self.application.path_folder
        if idx >= len(pathfolder):
            logger.debug('idx %s out of range for %s', idx, pathfolder)
            raise tornado.web.HTTPError(404)
        root, folder = pathfolder[idx]
        if root == '/':    # '/', 'home'
            path = root + folder
        elif folder:    # '/home', 'tyler'
            path = '/'.join((root, folder))
        else:   # '/', ''; 'C:', ''
            path = root
        path = '/'.join((path, sub)) if sub is not None else path
        return path

    def make_attr(self, path, targetdict, extradict={}):
        icon = self.application.icon
        if os.path.isdir(path):
            targetlist = targetdict.setdefault('folder', [])
            attrs = {'name': os.path.split(path)[-1],
                     'poster': icon['folder']}
        else:
            attrs = {'size': size(os.path.getsize(path))}
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

class HomeHandler(_Handler):
    def get(self):
        icon = self.application.icon['folder']
        shared = {}
        for idx, root_path in enumerate(self.application.path_folder):
            path = '/'.join(root_path) if root_path[1] else root_path[0]
            name = root_path[1] or root_path[0]
            if os.path.isdir(path):
                link = str(idx)+'/'
            else:
                link = str(idx)
            self.make_attr(path, shared, {'link': link, 'name': name, 'abspath': path})
        return self.render('home.html', detail=shared)

class FolderHandler(_Handler):
    def get(self, idx, subfoler=None):
        if subfoler is None:
            upper = False
        else:
            subfoler = unquote(subfoler)
            upper = True
        path = self._get_path(idx, subfoler)
        if os.path.isfile(path):
            uri = self.request.uri
            if not uri.endswith('/'):
                return self.redirect(uri+'/')
            logger.error('%s has no related folder or file', uri)
            raise tornado.web.HTTPError(500, '%s has no related folder or file'%uri)
        if not os.path.isdir(path):
            raise tornado.web.HTTPError(500, '%s has no related folder'%uri)

        detail = {}

        # listdir will not seperate the folders and files
        dirpath, dirnames, filenames = next(os.walk(path))
        ignore = self.application.ignore

        for eachdir in dirnames:
            thispath = '/'.join((path, eachdir))
            # for p in ignore:
            #     if fnmatch.fnmatch(eachdir+'/', p):
            #         logger.error('%s -> %s', eachdir+'/', p)
            #         break
            if any(map(lambda p: fnmatch.fnmatch(eachdir+'/', p), ignore)):
                logger.debug('%s is ignored', thispath)
                continue
            link = eachdir+'/'
            self.make_attr(thispath, detail, {'link': link, 'name': eachdir})
        for eachfile in filenames:
            if any(map(lambda p: fnmatch.fnmatch(eachfile, p), ignore)):
                logger.debug('%s is ignored', eachfile)
                continue
            thispath = '/'.join((path, eachfile))
            self.make_attr(thispath, detail, {'link': eachfile, 'name': eachfile})
        
        detail.setdefault('folder', []).insert(0, {'name': '..', 'link': '../', 'poster':self.application.icon['folder']})
        return self.render('show.html', detail=detail, path=path)

class FileHandler(_Handler):#, tornado.web.StaticFileHandler):

    @tornado.gen.coroutine
    def get(self, idx, subfoler=None):
        path = self._get_path(idx, subfoler)
        uri = self.request.uri
        if os.path.isdir(path) and not uri.endswith('/'):
            return self.redirect(uri+'/')

        self.set_header("Accept-Ranges", "bytes")
        mime, _ = mimetypes.guess_type(path)
        if mime is not None:
            self.set_header("Content-Type", mime)
        else:
            logger.info("unknow type %s", path)

        # -s=deal range
        request_range = None
        range_header = self.request.headers.get("Range")
        if range_header:
            # As per RFC 2616 14.16, if an invalid Range header is specified,
            # the request will be treated as if the header didn't exist.
            request_range = tornado.httputil._parse_request_range(range_header)

        size = os.path.getsize(path)
        logger.debug('file size: %s', size)
        if request_range:
            start, end = request_range
            if (start is not None and start >= size) or end == 0:
                # As per RFC 2616 14.35.1, a range is not satisfiable only: if
                # the first requested byte is equal to or greater than the
                # content, or when a suffix with length 0 is specified
                self.set_status(416)  # Range Not Satisfiable
                self.set_header("Content-Type", "text/plain")
                self.set_header("Content-Range", "bytes */%s" % (size, ))
                return
            if start is not None and start < 0:
                start += size
            if end is not None and end > size:
                # Clients sometimes blindly use a large range to limit their
                # download size; cap the endpoint at the actual file size.
                end = size
            # Note: only return HTTP 206 if less than the entire range has been
            # requested. Not only is this semantically correct, but Chrome
            # refuses to play audio if it gets an HTTP 206 in response to
            # ``Range: bytes=0-``.
            logger.debug('file from %s to %s', start, end)
            if size != (end or size) - (start or 0):
                self.set_status(206)  # Partial Content
                self.set_header("Content-Range",
                                tornado.httputil._get_content_range(start, end, size))
        else:
            start = end = None

        # -e=deal range

        # -s=deal content length
        if start is not None and end is not None:
            content_length = end - start
        elif end is not None:
            content_length = end
        elif start is not None:
            content_length = size - start
        else:
            content_length = size
        logger.debug('content length %s', content_length)
        self.set_header("Content-Length", content_length)
        # -e=deal content length

        # -s=write file
        content = self.get_content(path, start, end)
        if isinstance(content, bytes):
            content = [content]
        for chunk in content:
            try:
                self.write(chunk)
                yield self.flush()
            except tornado.iostream.StreamClosedError:
                return

    @classmethod
    def get_content(cls, abspath, start=None, end=None):
        """Retrieve the content of the requested resource which is located
        at the given absolute path.
        This class method may be overridden by subclasses.  Note that its
        signature is different from other overridable class methods
        (no ``settings`` argument); this is deliberate to ensure that
        ``abspath`` is able to stand on its own as a cache key.
        This method should either return a byte string or an iterator
        of byte strings.  The latter is preferred for large files
        as it helps reduce memory fragmentation.
        .. versionadded:: 3.1
        """
        with open(abspath, "rb") as file:
            if start is not None:
                file.seek(start)
            if end is not None:
                remaining = end - (start or 0)
            else:
                remaining = None
            while True:
                chunk_size = 64 * 1024
                if remaining is not None and remaining < chunk_size:
                    chunk_size = remaining
                chunk = file.read(chunk_size)
                if chunk:
                    if remaining is not None:
                        remaining -= len(chunk)
                    yield chunk
                else:
                    if remaining is not None:
                        assert remaining == 0
                    return
