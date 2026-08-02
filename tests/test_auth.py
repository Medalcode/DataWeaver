from datetime import timedelta
import pytest
from fastapi import HTTPException

from app.api.endpoints.auth import _validate_password_strength
from app.core.auth import (
    _decode_token,
    create_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing_and_verification():
    raw_password = "SecurePassword123!"
    hashed = get_password_hash(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_validate_password_strength_valid():
    # Should not raise any exception
    _validate_password_strength("Valid1234")


def test_validate_password_strength_too_short():
    with pytest.raises(HTTPException) as exc_info:
        _validate_password_strength("Short1")
    assert exc_info.value.status_code == 422
    assert "at least 8 characters" in exc_info.value.detail


def test_validate_password_strength_no_uppercase():
    with pytest.raises(HTTPException) as exc_info:
        _validate_password_strength("lowercase123")
    assert exc_info.value.status_code == 422
    assert "uppercase" in exc_info.value.detail


def test_validate_password_strength_no_lowercase():
    with pytest.raises(HTTPException) as exc_info:
        _validate_password_strength("UPPERCASE123")
    assert exc_info.value.status_code == 422
    assert "lowercase" in exc_info.value.detail


def test_validate_password_strength_no_number():
    with pytest.raises(HTTPException) as exc_info:
        _validate_password_strength("NoNumbersHere")
    assert exc_info.value.status_code == 422
    assert "number" in exc_info.value.detail


def test_jwt_token_create_and_decode():
    data = {"sub": "user-123", "company_id": "company-456"}
    token = create_access_token(data, expires_delta=timedelta(minutes=15))

    payload = _decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["company_id"] == "company-456"
    assert "exp" in payload


def test_jwt_token_invalid():
    with pytest.raises(HTTPException) as exc_info:
        _decode_token("invalid.jwt.token")
    assert exc_info.value.status_code == 401
