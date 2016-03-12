import re
import sys
import logging
import inspect
from flask import Flask, request, jsonify
from flask.blueprints import Blueprint

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class Api(object):
    def __init__(self, app):
        self.app = app

        # create routes
        route_comment = re.compile(r'(GET|PUT|POST|DELETE)\s*:\s*([^\s]+)', re.I)
        for method in inspect.getmembers(self, predicate=inspect.ismethod):
            match = route_comment.match(str(method[1].__doc__).strip())
            if match:
                verb = match.group(1)
                route = match.group(2)

                self.app.add_url_rule(
                    rule='/api/' + route,
                    endpoint=method[0],
                    view_func=self._endpoint_wrapper(method[1]),
                    methods=[verb]
                )
                logger.debug('Route created: %6s - %s' % (method, route))

    def _endpoint_wrapper(self, func):
        def run(*args, **kwargs):
            res = {'status': 'error', 'data': 'No data'}
            try:
                data = request.get_json(force=True, silent=True)
                res_data = func(data, *args, **kwargs)

                res = {
                    'status': 'ok',
                    'data': res_data
                }
            except Exception as err:
                res = {
                    'status': 'error',
                    'data': str(err)
                }
            finally:
                res = jsonify(res)
                res.headers['Access-Control-Allow-Origin'] = '*'
                res.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS, PUT, DELETE'
                res.headers['Access-Control-Allow-Headers'] = '*'
                res.headers['Access-Control-Max-Age'] = 1728000
                return res
        return run

    def hello_world(self, data):
        """
            GET: /
        """
        return 'Hello World'

    def user_create(self, data):
        """
            POST: /user
        """
        if 'email' not in data:
            raise Exception('No email send')

app = Flask(__name__)
api = Api(app)

if __name__ == '__main__':
    app.run()