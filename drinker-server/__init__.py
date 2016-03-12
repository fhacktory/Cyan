import re
import sys
import logging
import inspect
import mysql.connector
from mysql.connector import IntegrityError
from flask import Flask, request, jsonify

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
                route = '/api/' + match.group(2).lstrip('/')
                route = route.rstrip('/')

                self.app.add_url_rule(
                    rule=route,
                    endpoint=method[0],
                    view_func=self._endpoint_wrapper(method[1]),
                    methods=['OPTION', verb]
                )
                logger.debug('Route created: %6s - %s' % (verb, route))

    def _endpoint_wrapper(self, func):
        def run(*args, **kwargs):
            res = {'status': 'error', 'data': 'No data'}
            try:
                data = request.get_json(force=True, silent=True)
                res_data = func(data or {}, *args, **kwargs)

                res = {
                    'status': 'ok',
                    'data': res_data
                }
            except Exception as err:
                logger.exception(err)
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
        if 'first_name' not in data:
            raise Exception('No first_name send')
        if 'last_name' not in data:
            raise Exception('No last_name send')

        try:
            db_query("""
                INSERT INTO user (email, first_name, last_name)
                VALUES (%s, %s, %s);
            """, data['email'], data['first_name'], data['last_name'])
        except IntegrityError:
            return self.user_get(data, email=data['email'])
        except Exception:
            raise Exception('User creation fail')

        return self.user_get(data, email=data['email'])

    def user_get(self, data, email):
        """
            GET: /user/<email>
        """
        try:
            user = db_query("""
                SELECT * FROM user WHERE email = %s;
            """, email)[0]
        except IndexError:
            raise Exception('User not found')

        import hashlib
        email_hash = hashlib.md5(email.lower()).hexdigest()
        user['picture'] = 'http://www.gravatar.com/avatar/' + email_hash

        return user

    def user_update_coord(self, data, email):
        """
            PUT: /user/<email>
        """
        if 'latposition' not in data:
            raise Exception('No latposition send')
        if 'longposition' not in data:
            raise Exception('No longposition send')

        db_query("""
            UPDATE user SET latposition = %s, longposition = %s
            WHERE email = %s;
        """, data['latposition'], data['longposition'], email)

        return self.user_get(data, email=email)



app = Flask(__name__)
api = Api(app)

import mysql.connector
db = mysql.connector.connect(
    host='fhacktory.shep.fr',
    port=3333,
    user='root',
    passwd='root42',
    database='fhacktory'
)


def db_query(query, *args):
    logger.warn('DB QUERY: %s\n%s', query, args)
    cursor = None
    try:
        cursor = db.cursor()
        cursor.execute(query, args)
        if cursor.lastrowid is not None:
            db.commit()
            return cursor.lastrowid
        data = []
        for row in cursor.fetchall():
            data.append(dict(zip(cursor.column_names, row)))
        return data
    except Exception as err:
        logger.exception(err)
        raise err
    finally:
        if cursor:
            cursor.close()

if __name__ == '__main__':
    app.debug = True
    app.run()