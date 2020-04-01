from flask import render_template, flash, g, session, \
                  redirect, url_for, request, \
                  jsonify, Markup
from flask_login import current_user, login_required
from flask_babel import _, lazy_gettext as _l
from guess_language import guess_language
from app import db, get_locale
from . import bp
from app.models import User, Post
from .forms import EditProfileForm, PostForm
from .helper import paginate_posts
from app.translate import translate
from datetime import datetime


@bp.route("/")
def homepage():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return redirect(url_for("main.explore"))


@bp.route("/user/<username>/popup")
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("user_popup.html", user=user)

@bp.route("/index", methods=["GET", "POST"])
@login_required
def index():
    posts = current_user.followed_post()
    pagination = paginate_posts(posts, redirect_to="index")
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        language = language if language != "UNKNOWN" and len(language) <= 5 else ""
        post = Post(body=form.post.data,
                    author=current_user,
                    language=language)
        db.session.add(post)
        db.session.commit()
        flash(_l("Your post is now live!"))
        return redirect(url_for("main.index"))
    return render_template("index.html", title=_("Home"),
                           user=current_user, form=form, **pagination)


@bp.route("/explore")
def explore():
    posts = Post.query.order_by(Post.timestamp.desc())
    pagination = paginate_posts(posts, redirect_to="explore")
    if not current_user.is_authenticated:
        message = _(
            "You haven't signed in yet. <a href='%(login_url)s'>Login</a> " +
            "or <a href='%(register_url)s'>Sign up</a>.",
            login_url=url_for("auth.login"),
            register_url=url_for("auth.register")
        )
        markup = Markup(message)
        flash(markup)
    return render_template("explore.html", title=_("Explore"), **pagination)


@bp.route("/user/<username>")
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.timestamp.desc())
    pagination = paginate_posts(posts,
                                redirect_to="user",
                                username=user.username)
    return render_template("user.html", title=user.username,
                           user=user, **pagination)


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


@bp.route("/edit_profiles", methods=["GET", "POST"])
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.gender = form.gender.data
        db.session.commit()
        flash("Your update has been saved!")
        return(redirect(url_for("main.index")))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.gender.data = current_user.gender
    return render_template("edit_profile.html",
                           title=_("Edit Profile"),
                           form=form)


@bp.route("/follow/<username>")
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("User {} not found".format(username))
        return(redirect(url_for("main.index")))
    if user == current_user:
        flash("Dude you can't just follow yourself.")
        return(redirect(url_for("main.index")))
    current_user.follow(user)
    db.session.commit()
    flash("You've successfully followed {}.".format(username))
    return(redirect(url_for("main.user", username=username)))


@bp.route("/unfollow/<username>")
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("User {} not found".format(username))
        return(redirect(url_for("main.index")))
    if user == current_user:
        flash("Dude you can't just unfollow yourself.")
        return(redirect(url_for("main.index")))
    current_user.unfollow(user)
    db.session.commit()
    flash("You've successfully unfollowed {}.".format(username))
    return(redirect(url_for("main.user", username=username)))


@bp.route("/language/<language>")
def set_language(language):
    if current_user.is_authenticated:
        current_user.language = language
        db.session.commit()
    else:
        session["language"] = language
    return redirect(request.referrer or url_for("main.homepage"))


@bp.route("/translate", methods=["POST"])
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})


@login_required
@bp.route("/avatar", methods=["GET", "POST"])
def change_avatar():
    return render_template("avatar.html", user=current_user)
