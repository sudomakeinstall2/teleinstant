from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

import os
import json

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

with open(os.path.join(basedir, 'client_secrets.json')) as f:
    j = json.loads(f.read())
    app.config['client_secret'] = j['client_secret']
    app.config['redirect_uri'] = j['redirect_uri']
    app.config['client_id'] = j['client_id']

with open(os.path.join(basedir, 'secret_key.txt')) as f:
    key = f.read().strip()
    app.secret_key = key


db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

from app import views, models
