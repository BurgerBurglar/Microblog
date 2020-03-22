from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app.models import User, Post
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
from app.helper import paginate_posts
from app.email import send_password_reset_email
from datetime import datetime

@app.route("/")
def homepage():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return redirect(url_for("explore"))

@app.route("/index", methods=["GET", "POST"])
@login_required
def index():
    posts = current_user.followed_post()
    pagination = paginate_posts(posts, redirect_to="index")
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post is now live!")
        return redirect(url_for("index"))
    return render_template("index.html", title="HOME", user=current_user, form=form, **pagination)

@app.route("/explore")
def explore():
    posts = Post.query.order_by(Post.timestamp.desc())
    pagination = paginate_posts(posts, redirect_to="explore")
    return render_template("explore.html", title="Explore", **pagination)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
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
            return render_template("login.html", form=form)
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
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)
    pagination = paginate_posts(posts, redirect_to="user")
    return render_template("user.html", user=user, **pagination)

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
    
@app.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        flash("You are logged in. Redirecting to homepage")
        return(redirect(url_for("index")))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
            flash("Please check your inbox and spam folder for {}".format(user.email))
        return(redirect(url_for("login")))
    return render_template("reset_password_request.html", title="Reset Password",form=form)

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        logout_user()
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for("index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset successfully.")
        return redirect("login")
    return render_template("reset_password.html", form=form)
    
