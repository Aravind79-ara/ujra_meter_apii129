import asyncio

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
    try:
        app_main.settings.demo_mode = True
        app_main.client._authenticated = False

        with TestClient(app) as test_client:
            status = test_client.get("/api/v1/session")
            assert status.status_code == 200
            assert status.json()["authenticated"] is True
            assert status.json()["demo_mode"] is True

            login = test_client.post(
                "/api/v1/session/login",
                json={"username": "demo-user", "password": "demo-pass"},
            )
            assert login.status_code == 200
            assert login.json()["authenticated"] is True

            logout = test_client.post("/api/v1/session/logout")
            assert logout.status_code == 200
            assert logout.json()["authenticated"] is False
    finally:
        app_main.settings.demo_mode = original


def test_logout_keeps_configured_credentials_for_reauth():
    original_demo = app_main.settings.demo_mode
    original_user = app_main.settings.urja_username
    original_password = app_main.settings.urja_password
    try:
        app_main.settings.demo_mode = False
        app_main.settings.urja_username = "configured-user"
        app_main.settings.urja_password = "configured-pass"
        app_main.client._username = "configured-user"
        app_main.client._password = "configured-pass"
        app_main.client._authenticated = True

        asyncio.run(app_main.client.logout())

        assert app_main.client._authenticated is False
        assert app_main.client._username == "configured-user"
        assert app_main.client._password == "configured-pass"
    finally:
        app_main.settings.demo_mode = original_demo
        app_main.settings.urja_username = original_user
        app_main.settings.urja_password = original_password

