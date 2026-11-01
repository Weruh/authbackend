import pytest

from models import User


def test_password_is_private_and_hashed(app):
    user = User(username="tester")
    user.password_hash = "password123"
    assert user._password_hash != "password123"
    assert user.authenticate("password123")
    assert not user.authenticate("wrongpass")
    assert not user.authenticate(None)
    assert "password_hash" not in user.to_dict()
    with pytest.raises(AttributeError):
        _ = user.password_hash
    with pytest.raises(ValueError):
        user.password_hash = "é" * 37
