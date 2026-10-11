"""Өтінім логикасы (веб-бет пен API ортақ қолданады)."""
from .extensions import db
from .models import MentorRequest


def create_request(student, mentor, message):
    if mentor.free_slots <= 0:
        return None, "Бұл менторда бос орын жоқ."
    active = (
        MentorRequest.query.filter_by(student_id=student.id, mentor_id=mentor.id)
        .filter(MentorRequest.status.in_(["pending", "accepted"]))
        .first()
    )
    if active:
        return None, "Бұл ментормен белсенді өтініміңіз бар."
    req = MentorRequest(mentor_id=mentor.id, student_id=student.id, message=message)
    db.session.add(req)
    db.session.commit()
    return req, None


def can_view_request(user, req):
    if user.is_admin:
        return True
    if user.mentor and user.mentor.id == req.mentor_id:
        return True
    return bool(user.student and user.student.id == req.student_id)


def is_request_student(user, req):
    return user.is_admin or bool(user.student and user.student.id == req.student_id)


def change_status(req, new_status, user):
    """Қате мәтінін қайтарады, сәтті болса None."""
    is_mentor = bool(user.mentor and user.mentor.id == req.mentor_id)
    if new_status in ("accepted", "rejected"):
        if not (user.is_admin or is_mentor):
            return "Рұқсат жоқ."
    elif new_status == "cancelled":
        if not is_request_student(user, req):
            return "Рұқсат жоқ."
    else:
        return "Белгісіз статус."
    if req.status != "pending":
        return "Тек «Күтуде» статусындағы өтінімді өзгертуге болады."
    if new_status == "accepted" and req.mentor.free_slots <= 0:
        return "Бос орын қалмаған."
    req.status = new_status
    db.session.commit()
    return None
