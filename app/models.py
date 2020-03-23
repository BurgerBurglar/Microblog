from app import db, login, app
from datetime import datetime
from time import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
import jwt
from jwt.exceptions import DecodeError

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
    gender = db.Column(db.String(1), index=True)
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    post = db.relationship("Post", backref="author", lazy="dynamic")
    is_admin = db.Column(db.Boolean(), default=False)
    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.encode("utf-8")).hexdigest()
        # adroable avatar API is down
        return "https://api.adorable.io/avatars/{}/{}.png".format(size, digest)
        # gender_convert = {
        #     "M": "male",
        #     "F": "female",
        #     "B": "bottts"
        # }
        # return "https://avatars.dicebear.com/v2/{}/{}.svg?options[mood][]=happy" \
        #        .format(gender_convert[self.gender], digest)

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

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in}, 
            app.config["SECRET_KEY"],
            algorithm='HS256'
        ).decode("utf-8")

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token, 
                app.config["SECRET_KEY"], 
                algorithms=["HS256"]
            )["reset_password"]
        except DecodeError:
            return
        return User.query.get(id)

    def __repr__(self):
        return "<User {}>".format(self.username)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(280))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return "<Post {}>".format(self.body)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
