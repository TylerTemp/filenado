import tornado.web
import logging

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from base import BaseHandler
sys.path.pop(0)

logger = logging.getLogger('filenado.exchdlr')

class UrlFixOr404Handler(BaseHandler):
	def get(self):
		url = self.request.uri
		if not url.endswith('/'):
			red = url+'/'
			logger.debug('redirect %s to %s', url, red)
			return self.redirect(red)
		logger.critical('not found %s', url)
		raise tornado.web.HTTPError(404, 'Page Not Found')
