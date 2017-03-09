import threading
import os
import datetime
import telepot

from instagram.helper import datetime_to_timestamp

from models import User, UserLink

from instagram import client

from app import db, app

basedir = os.path.abspath(os.path.dirname(__file__))

class SendMessageThread(threading.Thread):
    def __init__(self, msg, chat_id):
        super(SendMessageThread, self).__init__()
        self.msg = msg
        self.chat_id = chat_id
        with open(os.path.join(basedir, '..', 'bot_token.txt'), 'r') as f:
            bot_token = f.read().strip()
            self.bot = telepot.Bot(bot_token)

    def run(self):
        self.bot.sendMessage(self.chat_id, self.msg)

        
class UpdateFollowerListThread(threading.Thread):
    def __init__(self, insta_id):
        super(UpdateFollowerListThread, self).__init__()
        self.insta_id = insta_id

    def run(self):
        user = User.query.filter_by(insta_id=self.insta_id).first()
        if not user:
            print 'insta_id %s not present' % self.insta_id
            return
        api = client.InstagramAPI(access_token=user.access_token, client_secret=app.config['client_secret'], client_id=app.config['client_id'])

        follows, next_ = api.user_follows()
        while next_:
            more_follows, next_ = api.user_follows(with_next_url=next_)
            follows.extend(more_follows)

        for fo in follows:
            link = UserLink.query.filter_by(from_insta_id=user.insta_id, to_insta_id=fo.id).first()
            if link:
                continue
            fuser = User.query.filter_by(insta_id=fo.id).first()
            if not fuser:
                fuser = User()
                fuser.insta_name = fo.username
                fuser.insta_id = fo.id
                db.session.add(fuser)
            userLink = UserLink()
            userLink.from_insta_id = user.insta_id
            userLink.to_insta_id = fo.id
            userLink.previous = datetime_to_timestamp(datetime.datetime.utcnow())
            db.session.add(userLink)
            db.session.commit()

#### end functions
