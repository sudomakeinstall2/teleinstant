from httplib2 import ServerNotFoundError

import telepot

import time, sys, datetime

from instagram import client
from instagram import InstagramAPIError
from instagram import InstagramClientError
from instagram.helper import timestamp_to_datetime, datetime_to_timestamp
from telepot.namedtuple import InlineKeyboardMarkup

from app import db, app

from app.models import User, UserLink


import os

from app.daemon import Daemon

import logging

logging.basicConfig(format='%(asctime)s %(message)s',
                    level=logging.INFO,
                    datefmt='%m/%d/%Y %I:%M:%S %p')
basedir = os.path.abspath(os.path.dirname(__file__))


class UpdateDaemon(Daemon):
    def run(self):
        with open(os.path.join(basedir, 'bot_token.txt'), 'r') as f:
            bot_token = f.read().strip()
        bot = telepot.Bot(bot_token)
        while True:
            users = User.query.all()
            for u in users:
                db.session.refresh(u)
                logging.info('checking user %s', u.insta_name)
                if not u.chat_id:
                    logging.info("user %s doesn't have chat_id", u.insta_name)
                    continue
                if not u.access_token:
                    logging.info("user %s doesn't have access code", u.insta_name)
                try:
                    api = client.InstagramAPI(access_token=u.access_token,
                                              client_secret=app.config['client_secret'],
                                              client_id=app.config['client_id'])

                    follows = UserLink.query.filter_by(from_insta_id=u.insta_id)
                    for fol in follows:
                        if not fol.previous:
                            logging.info("userlink %r doesn't have previous", fol)
                            continue
                        cur_time = datetime.datetime.utcnow()
                        recent_media, next_ = api.user_recent_media(user_id=fol.to_insta_id)
                        for media in recent_media:
                            if media.created_time < timestamp_to_datetime(fol.previous):
                                continue
                            caption = "%s:\n%s"%(media.caption.user.username, media.caption.text)
                            markup = InlineKeyboardMarkup(inline_keyboard=[
                              [dict(text='Image Link', url=media.link)]
                            ])
                            bot.sendPhoto(u.chat_id,
                                          photo=media.get_thumbnail_url(),
                                          caption=caption,
                                          reply_markup=markup)
                            # bot.sendMessage(u.chat_id, media.get_thumbnail_url())
                        fol.previous = datetime_to_timestamp(cur_time)
                        db.session.commit()
                except InstagramClientError as e:
                    logging.error("client exception: %r", e)
                except InstagramAPIError as e:
                    logging.error("api exception: %r", e)
                except ServerNotFoundError as e:
                    logging.error("server not found error: %r", e)

            logging.info("sleeping")
            sys.stdout.flush()
            time.sleep(120)


if __name__ == "__main__":
    daemon = UpdateDaemon(os.path.join(basedir, 'update_bot.pid'),
                          stdin='/dev/null',
                          stdout=os.path.join(basedir, 'update_bot.out'),
                          stderr=os.path.join(basedir, 'update_bot.err'))
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        elif 'run' == sys.argv[1]:
            daemon.run()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
