from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import app.main as app_main
from app.main import app


def test_consumption_boundary_is_explicit():
    original = app_main.settings.demo_mode
    try:
        app_main.settings.demo_mode = True
        with TestClient(app) as test_client:
            response = test_client.get("/api/v1/meters/MTR-101/consumption")
        assert response.status_code == 200
        assert response.json()["meter_id"] == "MTR-101"
    finally:
        app_main.settings.demo_mode = original


def test_meter_validation_error_uses_error_envelope():
    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/meters?page=0")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_demo_unknown_meter_returns_404():
    original = app_main.settings.demo_mode
    try:
        app_main.settings.demo_mode = True
        with TestClient(app) as test_client:
            response = test_client.get("/api/v1/meters/UNKNOWN/consumption")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "METER_NOT_FOUND"
    finally:
        app_main.settings.demo_mode = original


def test_session_status_and_login_logout_endpoints():
    original = app_main.settings.demo_mode
    original_auth = app_main.client._authenticated
    try:
        app_main.settings.demo_mode = True
        app_main.client._authenticated = False

        with TestClient(app) as test_client:
            status = test_client.get("/api/v1/session")
            assert status.status_code == 200
            assert status.json()["authenticated"] is False
            assert status.json()["demo_mode"] is True

            login = test_client.post(
                "/api/v1/session/login",
            )
            assert login.status_code == 200
            assert login.json()["authenticated"] is True
            assert test_client.get("/api/v1/session").json()["authenticated"] is True

            logout = test_client.post("/api/v1/session/logout")
            assert logout.status_code == 200
            assert logout.json()["authenticated"] is False
            assert test_client.get("/api/v1/session").json()["authenticated"] is False
    finally:
        app_main.settings.demo_mode = original
        app_main.client._authenticated = original_auth


def test_login_uses_configured_credentials_not_request_body(monkeypatch):
    monkeypatch.setattr(app_main.settings, "demo_mode", False)
    monkeypatch.setattr(app_main.settings, "urja_username", "configured-user")
    monkeypatch.setattr(app_main.settings, "urja_password", "configured-pass")
    login = AsyncMock()
    monkeypatch.setattr(app_main.client, "login", login)

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/session/login",
            json={"username": "untrusted-user", "password": "untrusted-pass"},
        )

    assert response.status_code == 200
    login.assert_awaited_once_with()


def test_openapi_validation_errors_use_custom_error_response():
    schema = app.openapi()
    for path in (
        "/api/v1/meters",
        "/api/v1/meters/{meter_id}",
        "/api/v1/meters/{meter_id}/consumption",
    ):
        method = "post" if path.endswith("login") else "get"
        operation = schema["paths"][path][method]
        assert operation["responses"]["422"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ErrorResponse"

    login_operation = schema["paths"]["/api/v1/session/login"]["post"]
    assert "requestBody" not in login_operation
    assert "422" not in login_operation["responses"]

