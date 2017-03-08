from app import db


class UserLink(db.Model):
    __tablename__ = 'userlinks'

    userlink_id = db.Column(db.Integer, primary_key=True)
    from_insta_id = db.Column(db.Integer, db.ForeignKey('users.insta_id'))
    to_insta_id = db.Column(db.Integer)
    previous = db.Column(db.String(100))

    def __repr__(self):
        return '<UserLink from_insta_id=%r to_insta_id=%r previous=%r>' % (self.from_insta_id,
                                                                           self.to_insta_id, self.previous)


class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    insta_id = db.Column(db.String(120), unique=True)
    insta_name = db.Column(db.String(120), unique=True)
    access_token = db.Column(db.Text)
    chat_id = db.Column(db.String(120), unique=True)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.user_id)  # python 2
        except NameError:
            return str(self.user_id)  # python 3

    def __repr__(self):
        return '<User insta_name:%r insta_id:%r>' % (self.insta_name)
