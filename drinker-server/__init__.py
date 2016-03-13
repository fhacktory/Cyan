import hashlib
import json
import re
import sys
import logging
import inspect
import requests
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

        request.args = dict(request.args)
        request.args.update({
            'lat': data['latposition'],
            'long': data['longposition']
        })

        return self.bar_list(data)

    def bar_list(self, data):
        """
            GET: /bar
            Get bar list (optional: nearby user)
        """

        if 'lat' not in request.args or 'long' not in request.args:
            raise Exception('Motherfucka get da chopa !')

        # get closest bars
        data = json.loads(requests.get(
            'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
            '?location=%s,%s'
            '&type=bar'
            '&rankby=distance'
            '&key=AIzaSyCBWhYZccelEDuhaJAeGuTgtX5wp5D62G4'
            % (request.args.get('lat'), request.args.get('long'))
        ).content)

        datum = []
        # foreach, update db
        for result in data.get('results', {}):
            # get from db
            try:
                db_res = db_query("""
                    SELECT bar.*,  CAST(avg(rating.mark) as UNSIGNED) as mark FROM bar
                    LEFT JOIN rating ON bar.id = rating.bar_id
                    WHERE gmap_ref = %s
                    GROUP BY bar.id;
                """, result.get('place_id'))[0]
            except:
                logger.exception('DEBUG')
                # if not present insert
                loc = result.get('geometry', {}).get('location', {})
                db_id = db_query("""
                    INSERT INTO bar (name, latposition, longposition, description, gmap_ref)
                    VALUES (%s, %s, %s, %s, %s);
                """,
                    result.get('name'),
                    loc.get('lat'),
                    loc.get('long'),
                    result.get('vicinity'),
                    result.get('place_id')
                )
                db_res = {
                    'id': db_id,
                    'name': result.get('name'),
                    'kind': None,
                    'latposition': loc.get('lat'),
                    'longposition': loc.get('long'),
                    'description': result.get('vicinity'),
                    'gmap_ref': result.get('place_id'),
                    'mark': None
                }

            # merge data
            photos = result.get('photos', [])
            if len(photos) is 0:
                photo = None
            else:
                photo = 'https://maps.googleapis.com/maps/api/place/photo' \
                '?maxwidth=400' \
                '&photoreference=%s' \
                '&key=AIzaSyCBWhYZccelEDuhaJAeGuTgtX5wp5D62G4'\
                % photos[0].get('photo_reference')
            db_res.update({
                'picture': photo,
                'open_now': result.get('opening_hours', {}).get('open_now', False),
                'types': result.get('types')
            })

            datum.append(db_res)

        return datum

    def bar_detail(self, data, bar_id):
        """
            GET: /bar/<int:bar_id>
            Get bar info
        """
        try:
            bar = db_query("""
            SELECT bar.*,  CAST(avg(rating.mark) as UNSIGNED) as mark FROM bar
            LEFT JOIN rating ON bar.id = rating.bar_id
            WHERE bar.id = %s
            GROUP BY bar.id;
            """, bar_id)[0]

        except:
            raise Exception('Bar not found')

        details = json.loads(requests.get('https://maps.googleapis.com/maps/api/place/details/json' \
        '?placeid=%s' \
        '&key=AIzaSyCBWhYZccelEDuhaJAeGuTgtX5wp5D62G4' \
        % bar.get('gmap_ref')).content).get('result', {})

        photos = details.get('photos', [])
        if len(photos) is 0:
            photo = None
        else:
            photo = 'https://maps.googleapis.com/maps/api/place/photo' \
                '?maxwidth=400' \
                '&photoreference=%s' \
                '&key=AIzaSyCBWhYZccelEDuhaJAeGuTgtX5wp5D62G4'\
            % photos[0].get('photo_reference')
        bar.update({
            'picture': photo,
            'open_now': details.get('opening_hours', {}).get('open_now', False),
            'types': details.get('types')
        })

        return bar

    def bar_rating(self, data, bar_id, rating):
        """
            GET: /bar/<bar_id>/<int:rating>
            Rate a bar (?user_id=XXX)

        """
        if rating < 0 or rating > 5:
            raise Exception('Rating must be rating < 0 or rating > 5')

        if 'user_id' not in request.args:
            raise Exception('No user')

        db_query("""
            INSERT INTO rating (mark, user_id, bar_id, drink_id)
            VALUES (%s, %s, %s, %s)
        """, rating,
             request.args.get('user_id'),
             bar_id,
             None)

        return 'OK'

    def drink_rating(self, data, drink_id, rating):
        """
            GET: /drink/<drink_id>/<int:rating>
            Rate a drink (?user_id=XXX)
        """
        if rating < 0 or rating > 5:
            raise Exception('Rating must be rating < 0 or rating > 5')

        if 'user_id' not in request.args:
            raise Exception('No user')

        db_query("""
            INSERT INTO rating (mark, user_id, bar_id, drink_id)
            VALUES (%s, %s, %s, %s)
        """, rating,
             request.args.get('user_id'),
             None,
             drink_id)

        return 'OK'

    def search_none(self, data, text):
        """
            GET: /search/
        """
        return {
            'bar': None,
            'drink': None
        }

    def search_bar_drink(self, data, text):
        """
            GET: /search/<text>
        """
        bars = db_query("""
            SELECT * FROM bar
            WHERE name LIKE upper('%%%s%%')
              OR description LIKE upper('%%%s%%')
              OR kind LIKE upper('%%%s%%')
            LIMIT 10;
        """ % (text, text, text))

        for bar in bars:
            details = json.loads(requests.get('https://maps.googleapis.com/maps/api/place/details/json' \
            '?placeid=%s' \
            '&key=AIzaSyCBWhYZccelEDuhaJAeGuTgtX5wp5D62G4' \
            % bar.get('gmap_ref')).content).get('result', {})

            photos = details.get('photos', [])
            if len(photos) is 0:
                photo = None
            else:
                photo = 'https://maps.googleapis.com/maps/api/place/photo' \
                    '?maxwidth=400' \
                    '&photoreference=%s' \
                    '&key=AIzaSyCBWhYZccelEDuhaJAeGuTgtX5wp5D62G4'\
                % photos[0].get('photo_reference')
            bar.update({
                'picture': photo,
                'open_now': details.get('opening_hours', {}).get('open_now', False),
                'types': details.get('types')
            })

        drinks = db_query("""
            SELECT * FROM drink
            WHERE upper(name) LIKE upper('%%%s%%')
              OR upper(description) LIKE upper('%%%s%%')
              OR upper(tags) LIKE upper('%%%s%%')
            LIMIT 10;
        """ % (text, text, text))

        users = db_query("""
            SELECT * FROM user
            WHERE upper(email) LIKE upper('%%%s%%')
              OR upper(first_name) LIKE upper('%%%s%%')
              OR upper(last_name) LIKE upper('%%%s%%')
            LIMIT 10;
        """ % (text, text, text))

        for user in users:
            email_hash = hashlib.md5(user.get('email').lower()).hexdigest()
            user['picture'] = 'http://www.gravatar.com/avatar/' + email_hash

        return {
            'bar': bars,
            'drink': drinks,
            'user': users
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

    def friend_add(self, data, user_mail, user_id):
        """
            GET: /friend/<user_id>/<user_mail>
            Add a new friend
        """

        db_query("""
             INSERT INTO friend ( user_id, friend_id, status)
             VALUES (%s, (SELECT id FROM user WHERE email = %s), 'pending');
        """, user_id, user_mail)

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

    def drink_request(self, data, user_id, friend_id, bar_id):
        """
            GET: /drink_request/<user_id>/<friend_id>/<bar_id>
            Ask a friend for a drink
        """

        db_query("""
            INSERT INTO request (user_id, friend_id, bar_id)
            VALUES (%s, %s, %s);
        """, user_id, friend_id, bar_id)

        return "Drink request sent"

    def drink_request_list(self, data, user_id):
        """
            GET: /drink_request/<user_id>/<friend_id>
            Ask a friend for a drink (optional: ?bar_id=X)
        """

        return db_query("""
            SELECT user.*, bar_id FROM user
            JOIN request ON request.friend_id = user.id
            WHERE request.user_id = %s;
        """, user_id)

    def drink_request_accept(self, data, drink_request):
        """
            GET: /drink_request/<drink_request>
            Accept drink request
        """

        db_query("""
            DELETE FROM request WHERE id = %s;
        """, drink_request)

        return "OK"


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