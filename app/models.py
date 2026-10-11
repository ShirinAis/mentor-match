from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager

DIRECTIONS = [
    "Веб-әзірлеу",
    "Деректер ғылымы",
    "Жасанды интеллект",
    "Киберқауіпсіздік",
    "Мобильді әзірлеу",
    "UI/UX дизайн",
    "Қаржы және бизнес",
    "Карьера және резюме",
]

STATUS_LABELS = {
    "pending": "Күтуде",
    "accepted": "Қабылданды",
    "rejected": "Қабылданбады",
    "cancelled": "Бас тартылды",
}


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="user")  # admin | user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    mentor = db.relationship("Mentor", backref="user", uselist=False)
    student = db.relationship("Student", backref="user", uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Mentor(db.Model):
    __tablename__ = "mentors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=True)
    full_name = db.Column(db.String(100), nullable=False)
    direction = db.Column(db.String(50), nullable=False)
    topics = db.Column(db.String(200), default="")
    bio = db.Column(db.Text, default="")
    experience_years = db.Column(db.Integer, default=0)
    max_students = db.Column(db.Integer, default=3)
    avatar = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    requests = db.relationship(
        "MentorRequest", backref="mentor", cascade="all, delete-orphan"
    )

    @property
    def accepted_count(self):
        return sum(1 for r in self.requests if r.status == "accepted")

    @property
    def free_slots(self):
        return max(self.max_students - self.accepted_count, 0)

    @property
    def topic_list(self):
        return [t.strip() for t in (self.topics or "").split(",") if t.strip()]

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "direction": self.direction,
            "topics": self.topic_list,
            "bio": self.bio,
            "experience_years": self.experience_years,
            "max_students": self.max_students,
            "free_slots": self.free_slots,
        }


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=True)
    full_name = db.Column(db.String(100), nullable=False)
    course = db.Column(db.Integer, default=1)
    interest = db.Column(db.String(50), nullable=False)
    goal = db.Column(db.Text, default="")
    phone = db.Column(db.String(25), default="")
    cv_file = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    requests = db.relationship(
        "MentorRequest", backref="student", cascade="all, delete-orphan"
    )


class MentorRequest(db.Model):
    __tablename__ = "requests"

    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey("mentors.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(12), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "mentor_id": self.mentor_id,
            "mentor": self.mentor.full_name,
            "student_id": self.student_id,
            "student": self.student.full_name,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
