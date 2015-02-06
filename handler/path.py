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
from lib.tool import format_size
sys.path.pop(0)

logger = logging.getLogger('filenado.path')


class HomeHandler(BaseHandler):
    def get(self):
        icon = self.application.icon['folder']
        shared = {}
        for idx, path in enumerate(self.application.paths):
            dirname, name = os.path.split(path)
            if not name:
                name = dirname
            if os.path.isdir(path):
                link = './%s/'%idx
            else:
                link = './%s'%idx
            self.make_attr(path, shared, {'link': link, 'name': name, 'abspath': path})
        
        _, idx, sub = self.get_act_idx_sub()
        switch = {}
        switch['Unix-Shell'] = '/'.join(('/fn', idx))
        switch['Regular'] = '/'.join(('/re', idx))

        return self.render('home.html', detail=shared, search=switch)


class FolderHandler(BaseHandler):

    def get(self):
        path = self.get_path()
        uri = self.request.uri
        if os.path.isfile(path) and not uri.endswith('/'):
            return self.redirect(uri[:-1])

        detail = self.parse_folder(path)
        detail.setdefault('folder', []).insert(0, {'name': '..', 'link': '../', 'poster':self.application.icon['folder']})
        _, idx, sub = self.get_act_idx_sub()
        switch = {}
        switch['Unix-Shell'] = '/'.join(('/fn', idx, sub))
        switch['Regular'] = '/'.join(('/re', idx, sub))
        return self.render('show.html', detail=detail, path=path, search=switch)

    def parse_folder(self, path):
        detail = {}
        _, idx, sub = self.get_act_idx_sub()
        # listdir will not seperate the folders and files
        dirpath, dirnames, filenames = next(os.walk(path))
        ignore = self.application.ignore

        for eachdir in dirnames:
            thispath = '/'.join((path, eachdir))
            if ignore and any(map(lambda p: fnmatch.fnmatch(eachdir+'/', p), ignore)):
                logger.debug('%s is ignored', thispath)
                continue
            link = './%s/'%eachdir
            self.make_attr(thispath, detail, {'link': link, 'name': eachdir})
        
        for eachfile in filenames:
            if ignore and any(map(lambda p: fnmatch.fnmatch(eachfile, p), ignore)):
                logger.debug('%s is ignored', eachfile)
                continue
            thispath = '/'.join((path, eachfile))
            self.make_attr(thispath, detail, {'link': eachfile, 'name': eachfile})
        
        return detail

class FileHandler(BaseHandler):#, tornado.web.StaticFileHandler):

    @tornado.gen.coroutine
    def get(self):
        path = self.get_path()
        uri = self.request.uri
        if os.path.isdir(path) and not uri.endswith('/'):
            self.redirect(uri+'/')
            return 

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
        logger.debug('file size: %s', format_size(size))
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

