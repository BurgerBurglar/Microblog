from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app.models import User
from app import app
from app.forms import LoginForm, RegistrationForm
import json
import os


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

@app.route("/register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Hello {}, welcome to Microblog!".format(user.name))
        login_user(user)
        return redirect(url_for("index"))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("index")
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
