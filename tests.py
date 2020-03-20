from datetime import datetime, timedelta
import unittest
from app import app, db
from app.models import User, Post
import tempfile


class UserModelCase(unittest.TestCase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite://'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_password_hash(self):
        u = User(username="肖战")
        u.set_password("xiaozhan")
        self.assertFalse(u.check_password("xiaochuan"))
        self.assertTrue(u.check_password("xiaozhan"))

    def test_avatar(self):
        u = User(username="鹿晗", email="luhan@gmail.com")
        self.assertEqual(
            u.avatar(128),
            "https://api.adorable.io/avatars/128/2bd2a01cc29163dff5f6d776f1bc36d6.png"
        )

    def test_follow(self):
        xiaozhan = User(username="肖战", email="xiaozhan@gmail.com")
        luhan = User(username="鹿晗", email="luhan@gmail.com")
        db.session.add(xiaozhan)
        db.session.add(luhan)
        db.session.commit()
        self.assertEqual(xiaozhan.followed.all(), [])
        self.assertEqual(luhan.followers.all(), [])

        xiaozhan.follow(luhan)
        db.session.commit()
        self.assertTrue(xiaozhan.is_following(luhan))
        self.assertEqual(xiaozhan.followed.count(), 1)
        self.assertEqual(xiaozhan.followed.first().username, "鹿晗")
        self.assertEqual(luhan.followers.count(), 1)
        self.assertEqual(luhan.followers.first().username, "肖战")

        xiaozhan.unfollow(luhan)
        db.session.commit()
        self.assertFalse(xiaozhan.is_following(luhan))
        self.assertEqual(xiaozhan.followed.count(), 0)
        self.assertEqual(luhan.followers.count(), 0)

    def test_follow_posts(self):
        xiaozhan = User(username="肖战", email="xiaozhan@gmail.com")
        luhan = User(username="鹿晗", email="luhan@gmail.com")
        guanxiaotong = User(username="关晓彤", email="guanxiaotong@gmail.com")
        wangyibo = User(username="王一博", email="wangyibo@gmail.com")
        db.session.add_all([
            xiaozhan,
            luhan,
            guanxiaotong,
            wangyibo
        ])

        now = datetime.utcnow()
        xiaozhan_p = Post(body="我是肖战", author=xiaozhan, timestamp=now + timedelta(seconds=1))
        luhan_p = Post(body="我是鹿晗", author=luhan, timestamp=now + timedelta(seconds=2))
        guanxiaotong_p = Post(body="我是关晓彤", author=guanxiaotong, timestamp=now + timedelta(seconds=3))
        wangyibo_p = Post(body="我是王一博", author=wangyibo, timestamp=now + timedelta(seconds=4))
        db.session.add_all([
            xiaozhan_p,
            luhan_p,
            guanxiaotong_p,
            wangyibo_p
        ])

        xiaozhan.follow(guanxiaotong)
        xiaozhan.follow(wangyibo)
        guanxiaotong.follow(luhan)
        guanxiaotong.follow(luhan)  # (again)
        luhan.follow(guanxiaotong)
        db.session.commit()

        xiaozhan_f = xiaozhan.followed_post().all() 
        luhan_f = luhan.followed_post().all()
        guanxiaotong_f = guanxiaotong.followed_post().all()
        wangyibo_f = wangyibo.followed_post().all()
        self.assertEqual(xiaozhan_f, [wangyibo_p, guanxiaotong_p, xiaozhan_p])
        self.assertEqual(luhan_f, [guanxiaotong_p, luhan_p])
        self.assertEqual(guanxiaotong_f, [guanxiaotong_p, luhan_p])
        self.assertEqual(wangyibo_f, [wangyibo_p])

    
if __name__ == "__main__":
    unittest.main(verbosity=2)
        
        

