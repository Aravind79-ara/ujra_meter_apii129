from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import app.main as app_main
from app.main import app


def test_meter_validation_error_uses_error_envelope():
    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/meters?page=0")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


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

    async def authenticate():
        app_main.client._authenticated = True

    login = AsyncMock(side_effect=authenticate)
    monkeypatch.setattr(app_main.client, "_authenticated", False)
    monkeypatch.setattr(app_main.client, "login", login)

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/session/login",
            json={"username": "untrusted-user", "password": "untrusted-pass"},
        )

    assert response.status_code == 200
    login.assert_awaited_once_with()


def test_live_meter_endpoint_uses_portal_json_pagination(monkeypatch):
    monkeypatch.setattr(app_main.settings, "demo_mode", False)
    first_page = {
        "data": [
            {
                "meterId": f"J{index:06d}",
                "serialNo": f"S{index:06d}",
                "make": "HPL",
                "phaseType": "single",
                "installStatus": "Installed",
                "dtCode": "DT-001",
            }
            for index in range(20)
        ],
        "total": 403,
        "page": 1,
        "pageSize": 20,
    }
    second_page = {
        **first_page,
        "data": [
            {
                "meterId": f"J{index:06d}",
                "serialNo": f"S{index:06d}",
                "make": "HPL",
                "phaseType": "single",
                "installStatus": "Installed",
                "dtCode": "DT-001",
            }
            for index in range(20, 40)
        ],
        "page": 2,
    }
    get_json = AsyncMock(side_effect=[first_page, second_page])
    monkeypatch.setattr(app_main.client, "get_json", get_json)

    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/meters?page_size=25")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 403
    assert len(body["items"]) == 25
    assert body["items"][0]["id"] == "J000000"
    assert body["items"][-1]["id"] == "J000024"
    assert body["items"][0]["make"] == "HPL"
    assert body["items"][0]["phase"] == "single"
    assert body["items"][0]["dt_code"] == "DT-001"
    assert get_json.await_args_list[0].args == (
        "/portal/meters/search?q=&page=1",
    )
    assert get_json.await_args_list[1].args == (
        "/portal/meters/search?q=&page=2",
    )


def test_live_hierarchy_reads_transformer_json(monkeypatch):
    monkeypatch.setattr(app_main.settings, "demo_mode", False)
    get_json = AsyncMock(
        return_value={
            "data": [
                {
                    "code": "DT-001",
                    "name": "Malviya Nagar DT 1",
                    "feederCode": "F-001",
                    "capacityKva": 100,
                }
            ],
            "total": 1,
            "page": 1,
            "pageSize": 20,
        }
    )
    monkeypatch.setattr(app_main.client, "get_json", get_json)

    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/hierarchy")

    assert response.status_code == 200
    node = response.json()["nodes"][0]
    assert node["id"] == "DT-001"
    assert node["label"] == "Malviya Nagar DT 1"
    assert node["feeder_code"] == "F-001"
    assert node["capacity_kva"] == 100
    get_json.assert_awaited_once_with("/portal/dts?page=1")


def test_openapi_validation_errors_use_custom_error_response():
    schema = app.openapi()
    for path in ("/api/v1/meters", "/api/v1/meters/{meter_id}"):
        operation = schema["paths"][path]["get"]
        assert operation["responses"]["422"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ErrorResponse"

    assert "/api/v1/meters/{meter_id}/consumption" not in schema["paths"]
    assert "Consumption" not in schema["components"]["schemas"]
    assert "Reading" not in schema["components"]["schemas"]

    login_operation = schema["paths"]["/api/v1/session/login"]["post"]
    assert "requestBody" not in login_operation
    assert "422" not in login_operation["responses"]
