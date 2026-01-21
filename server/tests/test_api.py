import pytest

from app import create_app
from models import db


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_signup_login_and_check_session(client):
    r = client.post(
        "/signup",
        json={
            "username": "lani",
            "password": "password",
            "password_confirmation": "password",
        },
    )
    assert r.status_code == 201
    data = r.get_json()
    assert data["username"] == "lani"

    r2 = client.get("/check_session")
    assert r2.status_code == 200
    assert r2.get_json()["username"] == "lani"

    r3 = client.delete("/logout")
    assert r3.status_code == 204

    r4 = client.get("/check_session")
    assert r4.status_code == 401


def test_notes_crud_and_protection(client):
    # not logged in
    r = client.get("/notes")
    assert r.status_code == 401

    # signup logs in
    client.post(
        "/signup",
        json={
            "username": "user1",
            "password": "password",
            "password_confirmation": "password",
        },
    )

    create = client.post("/notes", json={"title": "t1", "content": "c1"})
    assert create.status_code == 201
    note = create.get_json()

    idx = client.get("/notes?per_page=10&page=1")
    assert idx.status_code == 200
    payload = idx.get_json()
    assert payload["total"] == 1
    assert payload["notes"][0]["id"] == note["id"]

    upd = client.patch(f"/notes/{note['id']}", json={"title": "t2"})
    assert upd.status_code == 200
    assert upd.get_json()["title"] == "t2"

    show = client.get(f"/notes/{note['id']}")
    assert show.status_code == 200

    delete = client.delete(f"/notes/{note['id']}")
    assert delete.status_code == 204

    after = client.get("/notes")
    assert after.status_code == 200
    assert after.get_json()["total"] == 0


def test_users_cannot_access_each_others_notes(client, app):
    # user A
    client.post(
        "/signup",
        json={
            "username": "a",
            "password": "password",
            "password_confirmation": "password",
        },
    )
    n = client.post("/notes", json={"title": "a", "content": "a"}).get_json()
    client.delete("/logout")

    # user B
    client.post(
        "/signup",
        json={
            "username": "b",
            "password": "password",
            "password_confirmation": "password",
        },
    )

    r = client.get(f"/notes/{n['id']}")
    assert r.status_code == 404

    r2 = client.patch(f"/notes/{n['id']}", json={"title": "hack"})
    assert r2.status_code == 404

    r3 = client.delete(f"/notes/{n['id']}")
    assert r3.status_code == 404
