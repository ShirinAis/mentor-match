from functools import wraps

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user

from ..extensions import db
from ..forms import validate_message
from ..models import DIRECTIONS, Mentor, MentorRequest, User
from ..services import can_view_request, change_status, create_request, is_request_student

bp = Blueprint("api", __name__)


def api_login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify(error="Алдымен кіріңіз: POST /api/login"), 401
        return view(*args, **kwargs)

    return wrapper


def json_body():
    # Тек application/json қабылданады (cross-site форма жібере алмайды)
    if not request.is_json:
        return None
    return request.get_json(silent=True)


@bp.route("/login", methods=["POST"])
def api_login():
    body = json_body()
    if not isinstance(body, dict):
        return jsonify(error="JSON дене қажет"), 400
    user = User.query.filter_by(username=str(body.get("username", ""))).first()
    if not user or not user.check_password(str(body.get("password", ""))):
        return jsonify(error="Логин немесе құпиясөз қате"), 401
    login_user(user)
    return jsonify(message="OK", username=user.username, role=user.role)


@bp.route("/mentors", methods=["GET"])
def mentors():
    q = request.args.get("q", "").strip()
    direction = request.args.get("direction", "")
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 50)
    query = Mentor.query
    if q:
        query = query.filter(Mentor.full_name.ilike(f"%{q}%"))
    if direction in DIRECTIONS:
        query = query.filter(Mentor.direction == direction)
    p = query.order_by(Mentor.full_name).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(items=[m.to_dict() for m in p.items], page=p.page, pages=p.pages, total=p.total)


@bp.route("/mentors/<int:mentor_id>", methods=["GET"])
def mentor_one(mentor_id):
    return jsonify(db.get_or_404(Mentor, mentor_id).to_dict())


@bp.route("/requests", methods=["GET"])
@api_login_required
def requests_list():
    query = MentorRequest.query
    if current_user.is_admin:
        pass
    elif current_user.mentor:
        query = query.filter_by(mentor_id=current_user.mentor.id)
    elif current_user.student:
        query = query.filter_by(student_id=current_user.student.id)
    else:
        return jsonify(items=[])
    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)
    items = query.order_by(MentorRequest.created_at.desc()).all()
    return jsonify(items=[r.to_dict() for r in items])


@bp.route("/requests", methods=["POST"])
@api_login_required
def requests_create():
    body = json_body()
    if not isinstance(body, dict):
        return jsonify(error="JSON дене қажет"), 400
    if not current_user.student:
        return jsonify(error="Тек студент өтінім жібере алады"), 403
    mentor = db.session.get(Mentor, body.get("mentor_id")) if isinstance(body.get("mentor_id"), int) else None
    if not mentor:
        return jsonify(error="mentor_id қате"), 400
    message, err = validate_message(body.get("message"))
    if err:
        return jsonify(error=err), 400
    req, err = create_request(current_user.student, mentor, message)
    if err:
        return jsonify(error=err), 409
    return jsonify(req.to_dict()), 201


@bp.route("/requests/<int:req_id>", methods=["PUT"])
@api_login_required
def requests_update(req_id):
    req = db.get_or_404(MentorRequest, req_id)
    if not can_view_request(current_user, req):
        return jsonify(error="Рұқсат жоқ"), 403
    body = json_body()
    if not isinstance(body, dict):
        return jsonify(error="JSON дене қажет"), 400
    if "status" in body:
        err = change_status(req, str(body["status"]), current_user)
        if err:
            return jsonify(error=err), 400
    if "message" in body:
        if not is_request_student(current_user, req) or req.status != "pending":
            return jsonify(error="Хабарламаны тек студент, «Күтуде» кезінде өзгерте алады"), 403
        message, err = validate_message(body["message"])
        if err:
            return jsonify(error=err), 400
        req.message = message
        db.session.commit()
    return jsonify(req.to_dict())


@bp.route("/requests/<int:req_id>", methods=["DELETE"])
@api_login_required
def requests_delete(req_id):
    req = db.get_or_404(MentorRequest, req_id)
    if not is_request_student(current_user, req):
        return jsonify(error="Рұқсат жоқ"), 403
    db.session.delete(req)
    db.session.commit()
    return jsonify(message="Өшірілді")
