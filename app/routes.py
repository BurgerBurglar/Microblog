from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app.models import User, Post
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
import json
import os
from datetime import datetime


def get_data(dtype):
    file_dir = os.path.dirname(__file__)
    db_file = os.path.join(file_dir, "data.json")
    with open(db_file) as f:
        data = json.load(f)[dtype]
    return data


@app.route("/")
@app.route("/index")
@login_required
def index():
    if current_user.is_authenticated:
        user = current_user
    else:
        user = User(username="新朋友")
    posts = get_data("posts")
    return render_template("index.html", title="HOME", user=user, posts=posts)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        pass
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Hello {}, welcome to Microblog!".format(user.username))
        login_user(user)
        return redirect(url_for("index"))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":  # don't redirect to another domain
            next_page = url_for("index")
        return redirect(next_page)
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).all()
    return render_template("user.html", user=user, posts=posts)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route("/edit_profiles", methods=["GET", "POST"])
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your update has been saved!")
        return(redirect(url_for("index")))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", title="Edit Profile", form=form)

@app.route("/follow/<username>")
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("User {} not found".format(username))
        return(redirect(url_for("index")))
    if user == current_user:
        flash("Dude you can't just follow yourself.")
        return(redirect(url_for("index")))
    current_user.follow(user)
    db.session.commit()
    flash("You've successfully followed {}.".format(username))
    return(redirect(url_for("user", username=username)))

@app.route("/unfollow/<username>")
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("User {} not found".format(username))
        return(redirect(url_for("index")))
    if user == current_user:
        flash("Dude you can't just unfollow yourself.")
        return(redirect(url_for("index")))
    current_user.unfollow(user)
    db.session.commit()
    flash("You've successfully unfollowed {}.".format(username))
    return(redirect(url_for("user", username=username)))


        