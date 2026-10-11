import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DB_DIR = os.path.join(basedir, "instance")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        "sqlite:///" + os.path.join(DB_DIR, "mentor_match.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Файл жүктеу
    AVATAR_FOLDER = os.path.join(basedir, "app", "static", "uploads", "avatars")
    CV_FOLDER = os.path.join(basedir, "instance", "cv")  # static емес: жабық папка
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "webp"}
    ALLOWED_DOC_EXT = {"pdf"}

    # Пагинация
    PER_PAGE = 6
