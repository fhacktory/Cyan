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
        route_comment = re.compile(r'(GET|PUT|POST|DELETE)\s*:\s*([^\s]+)\s*(.*)', re.I)
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
                logger.debug('Route created: %6s - %-35s %s' % (verb, route, match.group(3)))

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
            Return hello world
        """
        return 'Hello World'

    def user_create(self, data):
        """
            POST: /user
            Create new user (body: email, first_name, last_name)
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
            Get user info
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
            Update user coordinates
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

    def bar_list(self, data):
        """
            GET: /bar
            Get bar list (optional: nearby user)
        """
        bars = db_query("""
            SELECT bar.*, avg(rating.mark) as mark FROM bar
            LEFT JOIN rating ON bar.id = rating.bar_id
            GROUP BY bar.id;
        """)

        return bars

    def bar_detail(self, data, bar_id):
        """
            GET: /bar/<int:bar_id>
            Get bar info
        """
        try:
            bar = db_query("""
            SELECT bar.*, avg(rating.mark) as mark FROM bar
            LEFT JOIN rating ON bar.id = rating.bar_id
            WHERE id = %s
            GROUP BY bar.id;
            """, bar_id)[0]
        except:
            raise Exception('Bar not found')

        return bar

    def bar_rating(self, data, bar_id, rating):
        """
            PUT: /bar/<bar_id>/<int:rating>
            Rate a bar (?user_id=XXX)

        """
        if rating < 0 or rating > 5:
            raise Exception('Rating must be rating < 0 or rating > 5')

        if 'user_id' not in request.args:
            raise Exception('No user')

        db_query("""
            INSERT INTO rating (mark, user_id, bar_id, drink_id)
            VALUES (%s, %s, %s, %s)
        """, request.args('user_id'),
             bar_id,
             None,
             rating)

        return 'OK'

    def drink_rating(self, data, drink_id, rating):
        """
            PUT: /drink/<drink_id>/<int:rating>
            Rate a drink (?user_id=XXX)
        """
        if rating < 0 or rating > 5:
            raise Exception('Rating must be rating < 0 or rating > 5')

        if 'user_id' not in request.args:
            raise Exception('No user')

        db_query("""
            INSERT INTO rating (mark, user_id, bar_id, drink_id)
            VALUES (%s, %s, %s, %s)
        """, request.args('user_id'),
             None,
             drink_id,
             rating)

        return 'OK'

    def search_bar_drink(self, data, text):
        """
            GET: /search/<text>
        """
        bars = db_query("""
            SELECT * FROM bar
            WHERE upper(name) LIKE upper(%s)
              AND upper(description) LIKE upper(%s)
              AND upper(kind) LIKE upper(%s);
        """, text, text, text)

        drinks = db_query("""
            SELECT * FROM drink
            WHERE upper(name) LIKE upper(%s)
              AND upper(description) LIKE upper(%s)
              AND upper(tags) LIKE upper(%s);
        """, text, text, text)

        return {
            'bar': bars,
            'drink': drinks
        }

    def get_friends(self, data):
        """
            GET: /friend
            List user's friends
        """

        if 'user_id' not in request.args:
            raise Exception('No user')

        current_friends = db_query("""
            SELECT * FROM user
            JOIN friend ON user.id = friend.friend_id OR user.id = friend.user_id
            WHERE friend.status = 'accepted'
             AND user.id = %s;
        """, request.args.get('user_id'))

        requested_friends = db_query("""
            SELECT * FROM user
            JOIN friend ON user.id = friend.user_id
            WHERE friend.status = 'pending'
             AND user.id = %s;
        """, request.args.get('user_id'))

        pending_friends = db_query("""
            SELECT * FROM user
            JOIN friend ON user.id = friend.friend_id
            WHERE friend.status = 'pending'
             AND user.id = %s;
        """, request.args.get('user_id'))

        return {
            'current': current_friends,
            'request': requested_friends,
            'pending': pending_friends
        }

    def friend_add(self, data, user_mail):
        """
            GET: /friend/<user_mail>
            Add a new friend (?user_id=XXX)
        """

        if 'user_id' not in request.args:
            raise Exception('No user')

        db_query("""
             INSERT INTO friend ( user_id, friend_id, status)
             VALUES (%s, (SELECT id FROM user WHERE email = %s), 'pending');
        """, request.args.get('user_id'), user_mail)

        return "Friend request sent"

    def friend_accept(self, data, friend_id):
        """
            GET: /friend/<friend_id>
            Accept a friend request
        """

        db_query("""
             UPDATE friend SET status = 'accepted' WHERE id = %s;
        """, friend_id)

        return "Friend request accepted"

    def drink_list(self, data):
        """
            GET: /drink
            List drinks (optional: ?bar_id=XXX)
        """

        if 'bar_id' not in request.args:
            drinks = db_query("""
                 SELECT * FROM drink WHERE bar_id = %s;
            """, request.args.get('bar_id'))
        else:
            drinks = db_query("""
                 SELECT * FROM drink;
            """)

        return drinks


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