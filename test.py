from app import db
from app.models import User, Post

user = User.query.get(1)
user.set_password("yiyangqianxi")
user.check_password("yiyangqianxi")
db.session.commit()
print(user, user.password_hash)