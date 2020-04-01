from flask import redirect, url_for, render_template, flash, Markup, g, request
from flask_login import current_user, login_user, logout_user
from flask_babel import _
from werkzeug.urls import url_parse
from app import db
from .forms import (
    LoginForm,
    RegistrationForm,
    ResetPasswordForm,
    ResetPasswordRequestForm,
)
from app.models import User
from . import bp
from .email import (
    send_password_reset_email,
    send_register_confirmation_email
)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.language = g.locale
        db.session.add(user)
        db.session.commit()
        confirm_registration_request(user.username)
        return redirect(url_for("auth.login"))
    return render_template("register.html", title=_("Register"), form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return render_template("login.html", form=form)
        if not user.is_verified:
            message = _("You haven't verified yet. <a href='%(url)s'>Verify now.</a>",
                        url=url_for("auth.confirm_registration_request",
                                    username=user.username))
            markup = Markup(message)
            flash(markup)
            return redirect(url_for("auth.login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            # don't redirect to another domain
            next_page = url_for("main.index")
        return redirect(next_page)
    return render_template("login.html", form=form)


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        flash("You are logged in. Redirecting to homepage")
        return(redirect(url_for("main.index")))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
            flash(_("Please check your inbox and spam folder for %(email)s",
                    email=user.email))
            return(redirect(url_for("auth.login")))
        else:
            flash(_("We couldn't find any account relating to this email. Try again?"))
    return render_template("reset_password_request.html",
                           title=_("Reset Password"), form=form)


@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        logout_user()
    user = User.verify_hash_token(token)
    if not user:
        return redirect(url_for("main.index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset successfully.")
        return redirect("login")
    return render_template("reset_password.html", form=form)


@bp.route("/confirm_registration_request/<username>")
def confirm_registration_request(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return render_template("errors/404.html"), 404
    if user.is_verified:
        flash(_("You're already verified. Let's go!"))
        return redirect(url_for("main.homepage"))
    send_register_confirmation_email(user)
    flash(_("Please check the inbox of %(email)s.", email=user.email))
    logout_user()
    return redirect(url_for("auth.login"))


@bp.route("/confirm_registration/<token>")
def confirm_registration(token):
    if current_user.is_authenticated:
        logout_user()
    user = User.verify_hash_token(token)
    if not user:
        flash(_("Your reset link is either invalid or expired."))
        return redirect(url_for("auth.login"))
    user.is_verified = True
    db.session.commit()
    flash(_("Hello %(username)s, welcome to Microblog!",
            username=user.username))
    return redirect(url_for("auth.login"))
