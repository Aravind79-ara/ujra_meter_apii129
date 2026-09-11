from fastapi.testclient import TestClient

from app.main import app


def test_consumption_boundary_is_explicit():
    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/meters/MTR-1/consumption")
    assert response.status_code == 200
    assert response.json()["meter_id"] == "MTR-1"


def test_meter_validation_error_uses_error_envelope():
    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/meters?page=0")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_session_login_and_logout():
    with TestClient(app) as test_client:
        login = test_client.post("/api/v1/session/login", json={"username": "demo@example.com", "password": "demo-password"})
        assert login.status_code == 200
        assert login.json()["authenticated"] is True
        logout = test_client.post("/api/v1/session/logout")
        assert logout.status_code == 200
        assert logout.json()["authenticated"] is False
