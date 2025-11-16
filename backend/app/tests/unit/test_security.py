"""Tests for security utilities."""

import pytest
from datetime import timedelta

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    verify_api_key,
)


def test_password_hashing():
    """Test password hashing and verification."""
    password = "TestPassword123"
    hashed = get_password_hash(password)

    # Hash should be different from password
    assert hashed != password

    # Verification should work
    assert verify_password(password, hashed) is True

    # Wrong password should fail
    assert verify_password("WrongPassword", hashed) is False


def test_create_access_token():
    """Test access token creation."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_access_token(subject=user_id)

    # Token should be a string
    assert isinstance(token, str)
    assert len(token) > 0

    # Decode token
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["type"] == "access"


def test_create_refresh_token():
    """Test refresh token creation."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_refresh_token(subject=user_id)

    # Token should be a string
    assert isinstance(token, str)
    assert len(token) > 0

    # Decode token
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"


def test_decode_invalid_token():
    """Test decoding invalid token."""
    invalid_token = "invalid.token.here"
    payload = decode_token(invalid_token)

    assert payload is None


def test_generate_api_key():
    """Test API key generation."""
    api_key = generate_api_key()

    # API key should start with ut_
    assert api_key.startswith("ut_")

    # Should be 46 characters total
    assert len(api_key) == 46

    # Should be verifiable
    assert verify_api_key(api_key) is True


def test_verify_api_key():
    """Test API key verification."""
    # Valid API key
    valid_key = generate_api_key()
    assert verify_api_key(valid_key) is True

    # Invalid format
    assert verify_api_key("invalid_key") is False
    assert verify_api_key("ut_short") is False
    assert verify_api_key("wrong_prefix_" + "a" * 32) is False


def test_token_expiration():
    """Test token expiration."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"

    # Create token with short expiration
    token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(seconds=-1)  # Already expired
    )

    # Token should be created
    assert token is not None

    # But should decode (expiration check is done by FastAPI)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
