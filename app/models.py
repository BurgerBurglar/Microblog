import json
from app import db, login
from datetime import datetime
from time import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
import jwt
from jwt.exceptions import DecodeError
from flask import current_app

followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id"))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    avatar = db.Column(db.String(400))
    gender = db.Column(db.String(1), index=True, default="B")
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    post = db.relationship("Post", backref="author", lazy="dynamic")
    is_admin = db.Column(db.Boolean(), default=False)
    language = db.Column(db.String(5), index=True)
    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic"
    )
    messages_sent = db.relationship(
        "Message",
        foreign_keys="Message.sender_id",
        backref="author",
        lazy="dynamic"
    )
    messages_received = db.relationship(
        "Message",
        foreign_keys="Message.recipient_id",
        backref="recipient",
        lazy="dynamic"
    )
    last_message_read_time = db.Column(db.DateTime)
    notifications = db.relationship("Notification", backref="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_avatar(self, size=128):
        if not self.avatar:
            digest = md5(self.email.encode("utf-8")).hexdigest()
            # adroable avatar API is down
            return "https://www.gravatar.com/avatar/{}?d=identicon&s={}.".format(digest, size)
            # gender_convert = {
            #     "M": "male",
            #     "F": "female",
            #     "B": "bottts"
            # }
            # return "https://avatars.dicebear.com/v2/{}/{}.svg?options[mood][]=happy" \
            #        .format(gender_convert[self.gender], digest)
        else:
            return self.avatar

    def is_following(self, other):
        return self in other.followers.all()

    def follow(self, other):
        if not self.is_following(other):
            self.followed.append(other)

    def unfollow(self, other):
        if self.is_following(other):
            self.followed.remove(other)

    def followed_post(self, n=None):
        own = self.post
        followed = Post.query \
                       .join(followers, followers.c.followed_id == Post.user_id) \
                       .filter(followers.c.follower_id == self.id)
        return followed.union(own) \
                       .order_by(Post.timestamp.desc()) \
                       .limit(n)

    def get_hash_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm='HS256'
        ).decode("utf-8")

    @staticmethod
    def verify_hash_token(token):
        try:
            id = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )["reset_password"]
        except DecodeError:
            return
        return User.query.get(id)

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query \
            .filter_by(recipient=self) \
            .filter(Message.timestamp > last_read_time) \
            .count()

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def __repr__(self):
        return "<User {}>".format(self.username)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(280))
    language = db.Column(db.String(5))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return "<Post {}>".format(self.body)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return "<Message ()>".format(self.body)

        
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.jsonify(str(self.payload_json))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
