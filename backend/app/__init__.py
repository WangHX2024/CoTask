"""Application factory."""
from __future__ import annotations

from flask import Flask, jsonify

from .config import get_config
from .extensions import api, configure_celery, cors, db, jwt, migrate, sock


def create_app(config_class=None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class or get_config())

    # ---- extensions ----
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    sock.init_app(app)
    api.init_app(app)
    configure_celery(app)

    # ---- import models so Alembic can detect them ----
    from . import models  # noqa: F401

    # ---- error handlers ----
    from .common.errors import register_error_handlers

    register_error_handlers(app)

    # ---- blueprints (smorest) ----
    from .modules.ai.routes import blp as ai_blp
    from .modules.auth.routes import blp as auth_blp
    from .modules.dashboard.routes import blp as dashboard_blp
    from .modules.discussion.routes import blp as discussion_blp
    from .modules.files.routes import blp as files_blp
    from .modules.groups.routes import blp as groups_blp
    from .modules.inspiration.routes import blp as inspiration_blp
    from .modules.notifications.routes import blp as notifications_blp
    from .modules.tasks.routes import blp as tasks_blp
    from .modules.timeline.routes import blp as timeline_blp
    from .modules.tree.routes import blp as tree_blp
    from .modules.users.routes import blp as users_blp

    for blp in (
        auth_blp,
        users_blp,
        groups_blp,
        tree_blp,
        tasks_blp,
        timeline_blp,
        dashboard_blp,
        inspiration_blp,
        files_blp,
        discussion_blp,
        notifications_blp,
        ai_blp,
    ):
        api.register_blueprint(blp)

    # ---- WebSocket ----
    from .modules.notifications.ws import register_ws

    register_ws(sock)

    # ---- health ----
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "cotask-api"})

    # ---- celery task discovery ----
    from . import tasks as _tasks  # noqa: F401

    return app
