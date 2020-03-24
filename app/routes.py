from flask import render_template, flash, g, session, \
                  redirect, url_for, request, Markup, \
                  jsonify
from flask_login import login_user, logout_user, current_user, login_required
from flask_babel import _, lazy_gettext as _l
from guess_language import guess_language
from werkzeug.urls import url_parse
from app.models import User, Post
from app import app, db, get_locale
from app.forms import LoginForm, RegistrationForm, EditProfileForm, \
                      PostForm, ResetPasswordRequestForm, ResetPasswordForm
from app.helper import paginate_posts
from app.email import send_password_reset_email, send_register_confirmation_email
from app.translate import translate
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
        language = guess_language(form.post.data)
        language = language if language != "UNKNOWN" and len(language) <= 5 else ""
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_l("Your post is now live!"))
        return redirect(url_for("index"))
    return render_template("index.html", title=_("Home"), user=current_user, form=form, **pagination)

@app.route("/explore")
def explore():
    posts = Post.query.order_by(Post.timestamp.desc())
    pagination = paginate_posts(posts, redirect_to="explore")
    if not current_user.is_authenticated:
        message = _(
            "You haven't signed in yet. <a href='%(login_url)s'>Login</a> or <a href='%(register_url)s'>Sign up</a>.",
            login_url=url_for("login"),
            register_url=url_for("register")
        )
        markup = Markup(message)
        flash(markup)
    return render_template("explore.html", title=_("Explore"), **pagination)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.language = g.locale
        db.session.add(user)
        db.session.commit()
        confirm_registration_request(user.username)
        return redirect(url_for("login"))
    return render_template("register.html", title=_("Register"), form=form)

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
        if not user.is_verified:
            message = _("You haven't verified yet. <a href='%(url)s'>Verify now.</a>", 
                        url=url_for("confirm_registration_request", username=user.username))
            markup = Markup(message)
            flash(markup)
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
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.timestamp.desc())
    pagination = paginate_posts(posts, redirect_to="user", username=user.username)
    return render_template("user.html", title=user.username, user=user, **pagination)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())

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
    return render_template("edit_profile.html", title=_("Edit Profile"), form=form)

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
        else:
            flash("We couldn't find any account relating to this email. Try again?")
    return render_template("reset_password_request.html", title=_("Reset Password"), form=form)

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        logout_user()
    user = User.verify_hash_token(token)
    if not user:
        return redirect(url_for("index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset successfully.")
        return redirect("login")
    return render_template("reset_password.html", form=form)

@app.route("/confirm_registration_request/<username>")
def confirm_registration_request(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return render_template("errors/404.html"), 404
    if user.is_verified:
        flash(_("You're already verified. Let's go!"))
        return redirect(url_for("homepage"))
    send_register_confirmation_email(user)
    flash(_("Please check the inbox of %(email)s.", email=user.email))
    logout_user()
    return redirect(url_for("login"))

@app.route("/confirm_registration/<token>")
def confirm_registration(token):
    if current_user.is_authenticated:
        logout_user()
    user = User.verify_hash_token(token)
    if not user:
        flash(_("Your reset link is either invalid or expired."))
        return redirect(url_for("login"))
    user.is_verified = True
    db.session.commit()
    flash("Hello {}, welcome to Microblog!".format(user.username))
    return redirect(url_for("login"))

@app.route("/language/<language>")
def set_language(language):
    if current_user.is_authenticated:
        current_user.language = language
        db.session.commit()
    else:
        session["language"] = language
    return redirect(request.referrer or url_for("homepage"))
    
@app.route("/translate", methods=["POST"])
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})
