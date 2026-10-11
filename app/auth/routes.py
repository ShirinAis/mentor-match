from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..forms import validate_register
from ..models import DIRECTIONS, Mentor, Student, User

bp = Blueprint("auth", __name__)


def safe_next(target):
    return target if target and target.startswith("/") and not target.startswith("//") else None


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    data, errors = {}, {}
    if request.method == "POST":
        data, errors = validate_register(request.form)
        if not errors:
            user = User(username=data["username"], email=data["email"], role="user")
            user.set_password(data["password"])
            db.session.add(user)
            db.session.flush()
            if data["account_type"] == "mentor":
                db.session.add(Mentor(user_id=user.id, full_name=data["full_name"],
                                      direction=DIRECTIONS[0], bio="Профильді толтырыңыз.",
                                      experience_years=0, max_students=3))
            else:
                db.session.add(Student(user_id=user.id, full_name=data["full_name"],
                                       interest=DIRECTIONS[0], course=1))
            db.session.commit()
            flash("Тіркелу сәтті! Енді кіріңіз.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html", v=data, errors=errors)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get("username", "").strip()).first()
        if user and user.check_password(request.form.get("password", "")):
            login_user(user)
            flash(f"Қош келдіңіз, {user.username}!", "success")
            return redirect(safe_next(request.args.get("next")) or url_for("main.index"))
        flash("Логин немесе құпиясөз қате.", "danger")
    return render_template("auth/login.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Жүйеден шықтыңыз.", "info")
    return redirect(url_for("main.index"))
