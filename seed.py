"""Add development examples without deleting existing records."""
from faker import Faker

from app import create_app
from extensions import db
from models import Note, User


def seed_database():
    fake = Faker()
    Faker.seed(42)
    created_users = created_notes = 0
    for username in ("alice", "bob"):
        if db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none():
            continue
        user = User(username=username)
        user.password_hash = "DemoPass123!"
        db.session.add(user)
        for _ in range(15):
            db.session.add(Note(title=fake.sentence(nb_words=5), content=fake.paragraph(), user=user))
            created_notes += 1
        created_users += 1
    db.session.commit()
    return created_users, created_notes


if __name__ == "__main__":
    with create_app().app_context():
        users, notes = seed_database()
        print(f"Created {users} users and {notes} notes.")
        print("Development credentials: alice or bob / DemoPass123!")
