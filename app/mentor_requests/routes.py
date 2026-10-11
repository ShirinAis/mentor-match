from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from ..extensions import db
from ..forms import validate_message
from ..models import STATUS_LABELS, Mentor, MentorRequest, Student
from ..services import can_view_request, change_status, create_request, is_request_student

bp = Blueprint("reqs", __name__)


@bp.route("/")
@login_required
def list_requests():
    status = request.args.get("status", "")
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "new")
    page = request.args.get("page", 1, type=int)

    query = MentorRequest.query.join(Mentor).join(Student)
    if current_user.is_admin:
        pass
    elif current_user.mentor:
        query = query.filter(MentorRequest.mentor_id == current_user.mentor.id)
    elif current_user.student:
        query = query.filter(MentorRequest.student_id == current_user.student.id)
    else:
        query = query.filter(db.false())
    if status in STATUS_LABELS:
        query = query.filter(MentorRequest.status == status)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Mentor.full_name.ilike(like), Student.full_name.ilike(like),
                                 MentorRequest.message.ilike(like)))
    order = MentorRequest.created_at.asc() if sort == "old" else MentorRequest.created_at.desc()
    pagination = query.order_by(order).paginate(
        page=page, per_page=current_app.config["PER_PAGE"], error_out=False)
    return render_template("requests.html", pagination=pagination, status=status, q=q, sort=sort)


@bp.route("/create/<int:mentor_id>", methods=["POST"])
@login_required
def create(mentor_id):
    mentor = db.get_or_404(Mentor, mentor_id)
    if not current_user.student:
        abort(403)
    message, err = validate_message(request.form.get("message"))
    if not err:
        _, err = create_request(current_user.student, mentor, message)
    if err:
        flash(err, "danger")
    else:
        flash("Өтінім жіберілді.", "success")
    return redirect(url_for("main.mentor_detail", mentor_id=mentor.id))


@bp.route("/<int:req_id>/status", methods=["POST"])
@login_required
def set_status(req_id):
    req = db.get_or_404(MentorRequest, req_id)
    if not can_view_request(current_user, req):
        abort(403)
    err = change_status(req, request.form.get("action", ""), current_user)
    flash(err or "Статус жаңартылды.", "danger" if err else "success")
    return redirect(request.referrer or url_for("reqs.list_requests"))


@bp.route("/<int:req_id>/edit", methods=["GET", "POST"])
@login_required
def edit(req_id):
    req = db.get_or_404(MentorRequest, req_id)
    if not is_request_student(current_user, req):
        abort(403)
    if req.status != "pending":
        flash("Тек «Күтуде» өтінімді өңдеуге болады.", "warning")
        return redirect(url_for("reqs.list_requests"))
    error = None
    if request.method == "POST":
        message, error = validate_message(request.form.get("message"))
        if not error:
            req.message = message
            db.session.commit()
            flash("Өтінім жаңартылды.", "success")
            return redirect(url_for("reqs.list_requests"))
    return render_template("request_edit.html", req=req, error=error,
                           text=request.form.get("message", req.message))


@bp.route("/<int:req_id>/delete", methods=["POST"])
@login_required
def delete(req_id):
    req = db.get_or_404(MentorRequest, req_id)
    if not is_request_student(current_user, req):
        abort(403)
    db.session.delete(req)
    db.session.commit()
    flash("Өтінім өшірілді.", "info")
    return redirect(url_for("reqs.list_requests"))
