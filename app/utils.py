import os
import uuid
from functools import wraps

from flask import abort, current_app
from flask_login import current_user

SIGNATURES = {
    "pdf": (b"%PDF",),
    "png": (b"\x89PNG",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "webp": (b"RIFF",),
}


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapper


def save_upload(file, folder, allowed):
    """Файлды қауіпсіз сақтайды. Қайтарады: (сақталған_аты | None, қате | None)."""
    if not file or not file.filename:
        return None, None
    ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if ext not in allowed:
        return None, "Рұқсат етілген түрлер: " + ", ".join(sorted(allowed))
    head = file.stream.read(12)
    file.stream.seek(0)
    if not any(head.startswith(sig) for sig in SIGNATURES.get(ext, ())):
        return None, "Файл мазмұны кеңейтіміне сәйкес келмейді."
    if ext == "webp" and head[8:12] != b"WEBP":
        return None, "Файл мазмұны кеңейтіміне сәйкес келмейді."
    name = f"{uuid.uuid4().hex}.{ext}"  # пайдаланушы атауы қолданылмайды
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, name))
    return name, None


def delete_upload(folder, name):
    if name:
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            os.remove(path)
