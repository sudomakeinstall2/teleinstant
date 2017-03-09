import datetime
import base64
import json

from app import app, db, lm

from flask_login import current_user, login_user, login_required, logout_user

import flask

from models import User, UserLink

from utils import UpdateFollowerListThread, SendMessageThread

from oauth2client import client

from instagram import client
from instagram.helper import timestamp_to_datetime, datetime_to_timestamp
from instagram.bind import InstagramClientError, InstagramAPIError

from hashing import make_secure

@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_request
def before_request():
    flask.g.user = current_user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'access_token' in flask.session and 'username' in flask.session:
        print 'access_token is in session'
        username = flask.session['username']
        user = User.query.filter_by(insta_name=username).first()
        if user:
            print 'user in database'
            user.access_token = flask.session['access_token']
            db.session.commit()
        else:
            print 'create new user in database'
            user = User()
            user.insta_name = username
            user.insta_id = flask.session['insta_id']
            user.access_token = flask.session['access_token']
            d = json.loads(base64.b64decode(flask.session['state']))
            user.chat_id = d['chat_id']
            db.session.add(user)
            db.session.commit()
            UpdateFollowerListThread(user.insta_id).start()

        SendMessageThread("Connected Successfully", user.chat_id).start()
        # remember = False
        # flask.session.pop('remember_me', None)
        flask.session.pop('state', None)
        flask.session.pop('access_token', None)
        flask.session.pop('username', None)
        # return """ Connected Successfuly <script> window.close();</script>"""
        return flask.redirect(flask.url_for('privacy'))
    else:
        return flask.redirect("http://t.me/teleinstantbot", code=302)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return flask.redirect(flask.url_for('login'))


@app.route('/')
def index():
    msg = """
    <h2>teleinstant</h2>
    <p>
    Using a telegram bot this application will notify you when there is new media in your feed
    by sending a low resolution image to your telegram account.
    </p>
    <p>
    In order to start you just have to send <b>/start</b> to <a href="http://t.me/teleinstantbot">
    teleinstant</a>.
    </p>
    <p>
    You can read our <a href="/privacy">pirvacy policy</a> and study our 
    <a href=https://github.com/sudomakeinstall2/teleinstant>code</a>.
    </p>
    """
    return msg


@app.route('/privacy')
def privacy():
    msg = """
    <h2> Privacy Policy </h2>
    <p>
    You don't have to take our word on this. <a href="http://t.me/teleinstantbot">teleinstant</a>
    is an <a href=https://github.com/sudomakeinstall2/teleinstant>open-source</a> application. Anyone can study and use it on their own server.
    </p>

    <h4> Sharing Data </h4>
    <p>
    We never share your data with anyone.
    </p>

    <h4> Storing Data </h4>
    <p>
    We only store the data we need to function properly. Including telegram's <i>chat_id</i>,
     instagram's <i>id</i>, <i>username</i> and <i>follower_list</i>. We never store your photos,
      comments or anything else.
    </p>

    <h4> Revoking Access </h4>
    <p>
    You can revoke your access anytime you want by going <a href="https://www.instagram.com/accounts/manage_access/">
    here</a>.
    </p>
    """
    return msg





@app.route('/oauthcallback')
def oauth2callback():
    code = flask.request.args.get('code')
    state = flask.request.args.get('state')
    if not code:
        return 'Missing code'
    if not state:
        return 'Missing state'
    try:
        unauthenticated_api = client.InstagramAPI(client_id=app.config['client_id'],
                                                  client_secret=app.config['client_secret'],
                                                  redirect_uri=app.config['redirect_uri'])
        access_token, user_info = unauthenticated_api.exchange_code_for_access_token(code)
        if not access_token:
            return 'Could not get access token'
        flask.session['access_token'] = access_token
        flask.session['username'] = user_info['username']
        flask.session['insta_id'] = user_info['id']
        flask.session['state'] = state
        return flask.redirect(flask.url_for('login'))
    except Exception as e:
        print "exception: ", e
        return e
