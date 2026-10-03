from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    password = "password123"

    password_hash = hash_password(
        password,
    )

    assert password_hash != password

    assert verify_password(
        password,
        password_hash,
    )

    assert not verify_password(
        "wrong-password",
        password_hash,
    )


def test_access_token():
    token = create_access_token(
        user_id="user-123",
        role="USER",
    )

    assert isinstance(
        token,
        str,
    )

    assert len(token) > 0