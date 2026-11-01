from extensions import db
from models import Note, User
from seed import seed_database


def test_seed_is_repeatable_and_preserves_existing_data(app):
    assert seed_database() == (2, 30)
    assert seed_database() == (0, 0)
    assert db.session.query(User).count() == 2
    assert db.session.query(Note).count() == 30
    for user in db.session.query(User).all():
        assert user.authenticate("DemoPass123!")
        assert len(user.notes) == 15
