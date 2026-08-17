from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from extensions import db
from models.user import User

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings")
def settings():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])

    return render_template(
        "settings/settings.html",
        user=user
    )


@settings_bp.route("/update-profile", methods=["POST"])
def update_profile():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])

    user.fullname = request.form["fullname"]
    user.mobile = request.form["mobile"]
    user.email = request.form["email"]
    user.village = request.form["village"]
    user.district = request.form["district"]
    user.state = request.form["state"]

    db.session.commit()

    flash("Profile Updated Successfully","success")

    return redirect(url_for("settings.settings"))


@settings_bp.route("/change-language/<lang>")
def change_language(lang):

    session["language"] = lang

    return redirect(url_for("settings.settings"))


@settings_bp.route("/notification", methods=["POST"])
def notification():

    session["notification"] = request.form.get("status")

    return "OK"


@settings_bp.route("/change-password", methods=["POST"])
def change_password():

    flash("Password Changed Successfully","success")

    return redirect(url_for("settings.settings"))
