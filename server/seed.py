from faker import Faker

import os
import sys

SERVER_DIR = os.path.abspath(os.path.dirname(__file__))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from app import app
from models import db, User, Note

fake = Faker()


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        users: list[User] = []
        for i in range(3):
            u = User(username=fake.user_name() + str(i))
            u.password_hash = "password"
            users.append(u)
        db.session.add_all(users)
        db.session.commit()

        notes: list[Note] = []
        for user in users:
            for _ in range(12):
                notes.append(
                    Note(
                        title=fake.sentence(nb_words=5),
                        content=fake.paragraph(nb_sentences=3),
                        user_id=user.id,
                    )
                )
        db.session.add_all(notes)
        db.session.commit()


if __name__ == "__main__":
    seed()
