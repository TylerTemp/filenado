import tornado.web
import logging
import mimetypes

logger = logging.getLogger('filenado.uimodule')

class FolderModule(tornado.web.UIModule):
    def render(self, name, link, poster, **_):
        return self.render_string(
                'ui/folder.html',
                name=name,
                link=link,
                poster=poster
            )

class ImageModule(tornado.web.UIModule):
    def render(self, name, link, size, **_):
        return self.render_string(
                'ui/image.html',
                name=name,
                link=link,
                size=size,
            )


class VideoModule(tornado.web.UIModule):
    def render(self, name, link, size, poster=None, **_):
        return self.render_string(
                'ui/video.html',
                name=name,
                link=link,
                poster=poster,
                size=size,
                mimetype=mimetypes.guess_type(link)[0]
            )

class AudioModule(tornado.web.UIModule):
    def render(self, name, link, size, poster=None, **_):
        return self.render_string(
            'ui/audio.html',
            name=name,
            link=link,
            poster=poster,
            size=size,
            mimetype=mimetypes.guess_type(link)[0]
        )

class UnknownModule(tornado.web.UIModule):
    def render(self, name, link, size,poster, **_):
        return self.render_string(
                'ui/unknown.html',
                name=name,
                link=link,
                size=size,
                poster=poster,
            )
