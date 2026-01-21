from __future__ import annotations

import math
import os
import sys

SERVER_DIR = os.path.abspath(os.path.dirname(__file__))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from flask import Flask, request, session
from flask_migrate import Migrate

from config import Config
from models import Note, User, bcrypt, db


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    bcrypt.init_app(app)
    Migrate(app, db)

    def current_user() -> User | None:
        user_id = session.get("user_id")
        if not user_id:
            return None
        return db.session.get(User, user_id)

    def require_login() -> User:
        user = current_user()
        if not user:
            from flask import abort
            abort(401)
        return user

    @app.errorhandler(401)
    def unauthorized(_err):
        return {"error": "Unauthorized"}, 401

    @app.errorhandler(404)
    def not_found(_err):
        return {"error": "Not Found"}, 404

    @app.post("/signup")
    def signup():
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        password_confirmation = data.get("password_confirmation") or ""

        errors: list[str] = []

        if not username:
            errors.append("Username is required")
        if not password:
            errors.append("Password is required")
        if password and password_confirmation and password != password_confirmation:
            errors.append("Password confirmation does not match")

        if username:
            existing = User.query.filter(User.username == username).first()
            if existing:
                errors.append("Username already exists")

        if errors:
            return {"errors": errors}, 422

        user = User(username=username)
        user.password_hash = password
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        return user.to_dict(), 201

    @app.post("/login")
    def login():
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        user = User.query.filter(User.username == username).first()
        if not user or not user.authenticate(password):
            return {"errors": ["Invalid username or password"]}, 401

        session["user_id"] = user.id
        return user.to_dict(), 200

    @app.delete("/logout")
    def logout():
        session.pop("user_id", None)
        return {}, 204

    @app.get("/check_session")
    def check_session():
        user = current_user()
        if not user:
            return {"errors": ["Not logged in"]}, 401
        return user.to_dict(), 200

    @app.get("/notes")
    def notes_index():
        user = require_login()

        page = request.args.get("page", "1")
        per_page = request.args.get("per_page", "10")

        try:
            page_i = max(int(page), 1)
        except ValueError:
            page_i = 1

        try:
            per_page_i = int(per_page)
        except ValueError:
            per_page_i = 10

        if per_page_i < 1:
            per_page_i = 10
        if per_page_i > 50:
            per_page_i = 50

        query = Note.query.filter(Note.user_id == user.id).order_by(Note.id.asc())
        total = query.count()
        pages = max(int(math.ceil(total / per_page_i)) if total else 1, 1)

        items = (
            query.offset((page_i - 1) * per_page_i)
            .limit(per_page_i)
            .all()
        )

        return {
            "notes": [n.to_dict() for n in items],
            "page": page_i,
            "per_page": per_page_i,
            "total": total,
            "pages": pages,
        }, 200

    @app.post("/notes")
    def notes_create():
        user = require_login()
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        content = (data.get("content") or "").strip()

        errors: list[str] = []
        if not title:
            errors.append("Title is required")
        if not content:
            errors.append("Content is required")

        if errors:
            return {"errors": errors}, 422

        note = Note(title=title, content=content, user_id=user.id)
        db.session.add(note)
        db.session.commit()
        return note.to_dict(), 201

    @app.get("/notes/<int:note_id>")
    def notes_show(note_id: int):
        user = require_login()
        note = db.session.get(Note, note_id)
        if not note or note.user_id != user.id:
            return {"error": "Not Found"}, 404
        return note.to_dict(), 200

    @app.patch("/notes/<int:note_id>")
    def notes_update(note_id: int):
        user = require_login()
        note = db.session.get(Note, note_id)
        if not note or note.user_id != user.id:
            return {"error": "Not Found"}, 404

        data = request.get_json(silent=True) or {}

        if "title" in data:
            title = (data.get("title") or "").strip()
            if not title:
                return {"errors": ["Title cannot be blank"]}, 422
            note.title = title

        if "content" in data:
            content = (data.get("content") or "").strip()
            if not content:
                return {"errors": ["Content cannot be blank"]}, 422
            note.content = content

        db.session.commit()
        return note.to_dict(), 200

    @app.delete("/notes/<int:note_id>")
    def notes_delete(note_id: int):
        user = require_login()
        note = db.session.get(Note, note_id)
        if not note or note.user_id != user.id:
            return {"error": "Not Found"}, 404

        db.session.delete(note)
        db.session.commit()
        return {}, 204

    return app


app = create_app()


if __name__ == "__main__":
    app.run(port=5555, debug=True)
