import sys
import time
import telepot
import os

from app import db

from app.models import User

from app.hashing import check_secure_val

from app.daemon import Daemon

import logging

logging.basicConfig(format='%(asctime)s %(message)s',
                    level=logging.INFO,
                    datefmt='%m/%d/%Y %I:%M:%S %p')
basedir = os.path.abspath(os.path.dirname(__file__))


class RegisterDaemon(Daemon):
    def register(self, code, chat_id):
        user_id = check_secure_val(code)
        if not user_id:
            logging.info("register failed because code is not right")
            return False
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            logging.info("register failed because user is not right")
            return False
        if not user.chat_id:
            logging.info("initializing user: setting chat id and previous")
            user.chat_id = chat_id
            self.bot.sendMessage(chat_id, 'successful registeration')

            db.session.commit()
            logging.info("successful register of %s", user.insta_name)
            return True
        logging.info("already registered %s", user.insta_name)
        return True

    def handle(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(content_type, chat_type, chat_id)

        if content_type == 'text':
            if msg['text'] == '/start':
                self.bot.sendMessage(chat_id, 'http://robotoos.ir:9000/login')
            elif msg['text'].split(' ')[0] == '/register':
                if len(msg['text'].split(' ')) != 2:
                    self.bot.sendMessage(chat_id, 'you need to send your registeration code')
                else:
                    if self.register(msg['text'].split(' ')[1], chat_id):
                        self.bot.sendMessage(chat_id, 'register successful')
                    else:
                        self.bot.sendMessage(chat_id, 'register failed')

    def run(self):
        with open(os.path.join(basedir, 'bot_token.txt'), 'r') as f:
            bot_token = f.read().strip()

        self.bot = telepot.Bot(bot_token)
        self.bot.message_loop(self.handle)
        logging.info('listening')

        # Keep the program running.
        while 1:
            time.sleep(120)
            sys.stdout.flush()


if __name__ == "__main__":

    daemon = RegisterDaemon(os.path.join(basedir, 'register_bot.pid'),
                            stdin='/dev/null',
                            stdout=os.path.join(basedir, 'register_bot.out'),
                            stderr=os.path.join(basedir, 'register_bot.err'))
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
