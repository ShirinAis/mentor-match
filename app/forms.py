"""Форма валидациясы: әр функция (тазаланған_деректер, қателер) қайтарады."""
import re

from .models import DIRECTIONS, Mentor, Student, User

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-()]{9,17}$")


def _get(form, key):
    return (form.get(key) or "").strip()


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def validate_register(form):
    d = {k: _get(form, k) for k in ("username", "email", "full_name", "account_type")}
    d["email"] = d["email"].lower()
    d["password"] = form.get("password") or ""
    e = {}
    if not USERNAME_RE.match(d["username"]):
        e["username"] = "Логин 3–30 символ: латын әріптері, сан және _."
    elif User.query.filter_by(username=d["username"]).first():
        e["username"] = "Бұл логин бос емес."
    if not EMAIL_RE.match(d["email"]) or len(d["email"]) > 120:
        e["email"] = "Дұрыс email енгізіңіз."
    elif User.query.filter_by(email=d["email"]).first():
        e["email"] = "Бұл email тіркелген."
    if not 2 <= len(d["full_name"]) <= 100:
        e["full_name"] = "Аты-жөні 2–100 символ болуы керек."
    if d["account_type"] not in ("student", "mentor"):
        e["account_type"] = "Тіркелу түрін таңдаңыз."
    pw = d["password"]
    if len(pw) < 8 or not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
        e["password"] = "Құпиясөз кемінде 8 символ, әріп және сан қамтуы керек."
    elif pw != (form.get("password2") or ""):
        e["password"] = "Құпиясөздер сәйкес емес."
    return d, e


def validate_mentor(form):
    d = {k: _get(form, k) for k in ("full_name", "direction", "topics", "bio")}
    e = {}
    if not 2 <= len(d["full_name"]) <= 100:
        e["full_name"] = "Аты-жөні 2–100 символ болуы керек."
    if d["direction"] not in DIRECTIONS:
        e["direction"] = "Тізімнен бағытты таңдаңыз."
    if len(d["topics"]) > 200:
        e["topics"] = "Тақырыптар 200 символдан аспауы керек."
    if not 10 <= len(d["bio"]) <= 1000:
        e["bio"] = "Өзі туралы 10–1000 символ болуы керек."
    exp = _int(form.get("experience_years"))
    if exp is None or not 0 <= exp <= 60:
        e["experience_years"] = "Тәжірибе 0–60 жыл аралығында."
    mx = _int(form.get("max_students"))
    if mx is None or not 1 <= mx <= 20:
        e["max_students"] = "Студент саны 1–20 аралығында."
    d["experience_years"], d["max_students"] = exp, mx
    return d, e


def validate_student(form):
    d = {k: _get(form, k) for k in ("full_name", "interest", "goal", "phone")}
    e = {}
    if not 2 <= len(d["full_name"]) <= 100:
        e["full_name"] = "Аты-жөні 2–100 символ болуы керек."
    if d["interest"] not in DIRECTIONS:
        e["interest"] = "Тізімнен бағытты таңдаңыз."
    if len(d["goal"]) > 500:
        e["goal"] = "Мақсат 500 символдан аспауы керек."
    if d["phone"] and not PHONE_RE.match(d["phone"]):
        e["phone"] = "Телефон форматы: +77011234567."
    course = _int(form.get("course"))
    if course is None or not 1 <= course <= 6:
        e["course"] = "Курс 1–6 аралығында."
    d["course"] = course
    return d, e


def validate_message(text):
    text = (text or "").strip()
    if not 10 <= len(text) <= 500:
        return text, "Хабарлама 10–500 символ болуы керек."
    return text, None
