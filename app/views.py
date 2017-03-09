import datetime
import base64
import json

from app import app, db, lm

from flask_login import current_user, login_user, login_required, logout_user

import flask

from models import User, UserLink

from utils import UpdateFollowerListThread

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

        remember = False
        flask.session.pop('remember_me', None)
        flask.session.pop('access_token', None)
        flask.session.pop('username', None)
        return """ Connected Successfuly <script> window.close();</script>"""
    


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return flask.redirect(flask.url_for('login'))


@app.route('/')
@login_required
def root():
    message = ""
    if flask.g.user and flask.g.user.is_authenticated:
        if flask.g.user.chat_id:
            message = "You are already registered."
        else:
            message = "Send this to @teleinstantbot in telegram:\n" + \
                      "<b>" + \
                      "/register " + \
                      make_secure(str(flask.g.user.user_id))
    return message


@app.route('/index')
@login_required
def index():
    content = "<h2>User Recent Media</h2>"
    access_token = flask.g.user.access_token
    try:
        api = client.InstagramAPI(access_token=access_token,
                                  client_secret=app.config['client_secret'],
                                  client_id=app.config['client_id'])

        photos = []
        follows = UserLink.query.filter_by(from_insta_id=flask.g.user.insta_id)

        for fol in follows:
            curtime = datetime.datetime.utcnow()
            print curtime
            recent_media, next_ = api.user_recent_media(user_id=fol.to_insta_id)
            for media in recent_media:
                if media.created_time < timestamp_to_datetime(fol.previous):
                    continue
                photos.append('<div style="float:left;">')
                if media.type == 'video':
                    photos.append('<video controls width height="150"><source type="video/mp4" src="%s"/></video>' % (
                        media.get_standard_resolution_url()))
                else:
                    photos.append('<img src="%s"/>' % (media.get_thumbnail_url()))
                photos.append(
                    "<br/> <a href='/media_like/%s'>Like</a>  <a href='/media_unlike/%s'>Un-Like</a>  LikesCount=%s Created=%s</div>" % (
                        media.id, media.id, media.like_count, media.created_time))
            fol.previous = datetime_to_timestamp(curtime)
            db.session.commit()
        content += ''.join(photos)

    except InstagramClientError as e:
        print "client exception: ", e
        return "error"
    except InstagramAPIError as e:
        print "api exception: ", e
        return "error"
    return content


@app.route('/callback')
def callback():
    return flask.request.args.get('code')


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
