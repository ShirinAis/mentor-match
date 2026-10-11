import os

from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, send_from_directory, url_for)
from flask_login import current_user, login_required
from sqlalchemy import or_

from ..extensions import db
from ..forms import validate_mentor, validate_student
from ..models import DIRECTIONS, Mentor, MentorRequest, Student
from ..utils import admin_required, delete_upload, save_upload

bp = Blueprint("main", __name__)

MENTOR_SORTS = {
    "name": Mentor.full_name.asc(),
    "exp": Mentor.experience_years.desc(),
    "new": Mentor.created_at.desc(),
}
STUDENT_SORTS = {
    "name": Student.full_name.asc(),
    "course": Student.course.asc(),
    "new": Student.created_at.desc(),
}


def can_edit_mentor(m):
    return current_user.is_admin or bool(current_user.mentor and current_user.mentor.id == m.id)


def can_edit_student(s):
    return current_user.is_admin or bool(current_user.student and current_user.student.id == s.id)


# ------------------------------------------------------------------ Mentors
@bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    direction = request.args.get("direction", "")
    sort = request.args.get("sort", "name")
    page = request.args.get("page", 1, type=int)

    query = Mentor.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Mentor.full_name.ilike(like), Mentor.topics.ilike(like),
                                 Mentor.bio.ilike(like)))
    if direction in DIRECTIONS:
        query = query.filter(Mentor.direction == direction)
    query = query.order_by(MENTOR_SORTS.get(sort, MENTOR_SORTS["name"]))
    pagination = query.paginate(page=page, per_page=current_app.config["PER_PAGE"], error_out=False)
    return render_template("index.html", pagination=pagination, q=q, direction=direction, sort=sort)


@bp.route("/mentors/<int:mentor_id>")
def mentor_detail(mentor_id):
    mentor = db.get_or_404(Mentor, mentor_id)
    my_request = None
    if current_user.is_authenticated and current_user.student:
        my_request = (MentorRequest.query.filter_by(mentor_id=mentor.id, student_id=current_user.student.id)
                      .order_by(MentorRequest.created_at.desc()).first())
    can_edit = current_user.is_authenticated and can_edit_mentor(mentor)
    return render_template("mentor_detail.html", mentor=mentor, my_request=my_request, can_edit=can_edit)


def mentor_values(m):
    return {k: getattr(m, k) for k in ("full_name", "direction", "topics", "bio",
                                      "experience_years", "max_students")}


def _save_mentor(mentor, data):
    for key in ("full_name", "direction", "topics", "bio", "experience_years", "max_students"):
        setattr(mentor, key, data[key])


@bp.route("/mentors/new", methods=["GET", "POST"])
@admin_required
def mentor_new():
    values, errors = {"experience_years": 0, "max_students": 3}, {}
    if request.method == "POST":
        values, errors = validate_mentor(request.form)
        avatar, err = save_upload(request.files.get("avatar"), current_app.config["AVATAR_FOLDER"],
                                  current_app.config["ALLOWED_IMAGE_EXT"])
        if err:
            errors["avatar"] = err
        if not errors:
            mentor = Mentor()
            _save_mentor(mentor, values)
            mentor.avatar = avatar
            db.session.add(mentor)
            db.session.commit()
            flash("Ментор қосылды.", "success")
            return redirect(url_for("main.mentor_detail", mentor_id=mentor.id))
        delete_upload(current_app.config["AVATAR_FOLDER"], avatar)
    return render_template("mentor_form.html", v=values, errors=errors, mentor=None)


@bp.route("/mentors/<int:mentor_id>/edit", methods=["GET", "POST"])
@login_required
def mentor_edit(mentor_id):
    mentor = db.get_or_404(Mentor, mentor_id)
    if not can_edit_mentor(mentor):
        abort(403)
    values, errors = mentor_values(mentor), {}
    if request.method == "POST":
        values, errors = validate_mentor(request.form)
        avatar, err = save_upload(request.files.get("avatar"), current_app.config["AVATAR_FOLDER"],
                                  current_app.config["ALLOWED_IMAGE_EXT"])
        if err:
            errors["avatar"] = err
        if not errors:
            _save_mentor(mentor, values)
            if avatar:
                delete_upload(current_app.config["AVATAR_FOLDER"], mentor.avatar)
                mentor.avatar = avatar
            db.session.commit()
            flash("Профиль жаңартылды.", "success")
            return redirect(url_for("main.mentor_detail", mentor_id=mentor.id))
        delete_upload(current_app.config["AVATAR_FOLDER"], avatar)
    return render_template("mentor_form.html", v=values, errors=errors, mentor=mentor)


@bp.route("/mentors/<int:mentor_id>/delete", methods=["POST"])
@admin_required
def mentor_delete(mentor_id):
    mentor = db.get_or_404(Mentor, mentor_id)
    delete_upload(current_app.config["AVATAR_FOLDER"], mentor.avatar)
    db.session.delete(mentor)
    db.session.commit()
    flash("Ментор өшірілді.", "info")
    return redirect(url_for("main.index"))


# ----------------------------------------------------------------- Students
@bp.route("/students")
@admin_required
def students():
    q = request.args.get("q", "").strip()
    course = request.args.get("course", type=int)
    sort = request.args.get("sort", "name")
    page = request.args.get("page", 1, type=int)
    query = Student.query
    if q:
        query = query.filter(Student.full_name.ilike(f"%{q}%"))
    if course:
        query = query.filter(Student.course == course)
    query = query.order_by(STUDENT_SORTS.get(sort, STUDENT_SORTS["name"]))
    pagination = query.paginate(page=page, per_page=current_app.config["PER_PAGE"], error_out=False)
    return render_template("students.html", pagination=pagination, q=q, course=course, sort=sort)


def student_values(s):
    return {k: getattr(s, k) for k in ("full_name", "course", "interest", "goal", "phone")}


def _save_student(student, data):
    for key in ("full_name", "course", "interest", "goal", "phone"):
        setattr(student, key, data[key])


@bp.route("/students/new", methods=["GET", "POST"])
@admin_required
def student_new():
    values, errors = {"course": 1}, {}
    if request.method == "POST":
        values, errors = validate_student(request.form)
        cv, err = save_upload(request.files.get("cv"), current_app.config["CV_FOLDER"],
                              current_app.config["ALLOWED_DOC_EXT"])
        if err:
            errors["cv"] = err
        if not errors:
            student = Student()
            _save_student(student, values)
            student.cv_file = cv
            db.session.add(student)
            db.session.commit()
            flash("Студент қосылды.", "success")
            return redirect(url_for("main.students"))
        delete_upload(current_app.config["CV_FOLDER"], cv)
    return render_template("student_form.html", v=values, errors=errors, student=None)


@bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def student_edit(student_id):
    student = db.get_or_404(Student, student_id)
    if not can_edit_student(student):
        abort(403)
    values, errors = student_values(student), {}
    if request.method == "POST":
        values, errors = validate_student(request.form)
        cv, err = save_upload(request.files.get("cv"), current_app.config["CV_FOLDER"],
                              current_app.config["ALLOWED_DOC_EXT"])
        if err:
            errors["cv"] = err
        if not errors:
            _save_student(student, values)
            if cv:
                delete_upload(current_app.config["CV_FOLDER"], student.cv_file)
                student.cv_file = cv
            db.session.commit()
            flash("Профиль жаңартылды.", "success")
            return redirect(url_for("main.index"))
        delete_upload(current_app.config["CV_FOLDER"], cv)
    return render_template("student_form.html", v=values, errors=errors, student=student)


@bp.route("/students/<int:student_id>/delete", methods=["POST"])
@admin_required
def student_delete(student_id):
    student = db.get_or_404(Student, student_id)
    delete_upload(current_app.config["CV_FOLDER"], student.cv_file)
    db.session.delete(student)
    db.session.commit()
    flash("Студент өшірілді.", "info")
    return redirect(url_for("main.students"))


@bp.route("/students/<int:student_id>/cv")
@login_required
def student_cv(student_id):
    student = db.get_or_404(Student, student_id)
    allowed = (can_edit_student(student)
               or (current_user.mentor and any(r.mentor_id == current_user.mentor.id
                                               for r in student.requests)))
    if not allowed or not student.cv_file:
        abort(404 if allowed else 403)
    return send_from_directory(current_app.config["CV_FOLDER"], student.cv_file)


# ------------------------------------------------------------------ Profile
@bp.route("/profile")
@login_required
def profile():
    if current_user.mentor:
        return redirect(url_for("main.mentor_edit", mentor_id=current_user.mentor.id))
    if current_user.student:
        return redirect(url_for("main.student_edit", student_id=current_user.student.id))
    flash("Әкімшіге жеке профиль қажет емес.", "info")
    return redirect(url_for("main.index"))
