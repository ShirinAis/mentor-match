import os
import secrets

from flask import Flask, abort, jsonify, render_template, request, session

from config import Config

from .extensions import db, login_manager
from .models import DIRECTIONS, STATUS_LABELS


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    for folder in (app.config["DB_DIR"], app.config["AVATAR_FOLDER"], app.config["CV_FOLDER"]):
        os.makedirs(folder, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Алдымен жүйеге кіріңіз."
    login_manager.login_message_category = "warning"

    from .api.routes import bp as api_bp
    from .auth.routes import bp as auth_bp
    from .main.routes import bp as main_bp
    from .mentor_requests.routes import bp as reqs_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(reqs_bp, url_prefix="/requests")
    app.register_blueprint(api_bp, url_prefix="/api")

    # --- CSRF (қарапайым, session негізінде) ---
    def csrf_token():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)
        return session["_csrf"]

    app.jinja_env.globals.update(
        csrf_token=csrf_token, STATUS_LABELS=STATUS_LABELS, DIRECTIONS=DIRECTIONS
    )

    @app.before_request
    def csrf_protect():
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and not request.path.startswith("/api/"):
            sent = request.form.get("_csrf", "")
            if not sent or not secrets.compare_digest(sent, session.get("_csrf", "")):
                abort(400)

    # --- Қате беттері ---
    def wants_json():
        return request.path.startswith("/api/")

    @app.errorhandler(404)
    def not_found(e):
        if wants_json():
            return jsonify(error="Табылмады"), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        if wants_json():
            return jsonify(error="Сервер қатесі"), 500
        return render_template("errors/500.html"), 500

    for code, text in ((400, "Сұраныс қате немесе сессия мерзімі өтті."),
                       (403, "Бұл әрекетке рұқсатыңыз жоқ."),
                       (413, "Файл тым үлкен (макс. 5 MB).")):
        def handler(e, code=code, text=text):
            if wants_json():
                return jsonify(error=text), code
            return render_template("errors/error.html", code=code, text=text), code
        app.register_error_handler(code, handler)

    # --- CLI ---
    @app.cli.command("init-db")
    def init_db():
        """Кестелерді құру."""
        db.create_all()
        print("Дерекқор дайын.")

    @app.cli.command("seed")
    def seed():
        """Тест деректерін толтыру."""
        from .seed import seed_data
        seed_data()
        print("Тест деректері қосылды.")

    with app.app_context():
        db.create_all()

    return app
