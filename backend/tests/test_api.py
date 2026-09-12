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

