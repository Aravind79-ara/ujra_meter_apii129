import pytest

from app.parsers import parse_meters, parse_portal_meters, parse_portal_transformers


def test_parse_portal_meter_api_records():
    meters, total, page_size = parse_portal_meters(
        {
            "data": [
                {
                    "meterId": "J100000",
                    "serialNo": "SE33962",
                    "make": "HPL",
                    "phaseType": "single",
                    "installStatus": "Decommissioned",
                    "dtCode": "DT-001",
                }
            ],
            "total": 403,
            "page": 1,
            "pageSize": 20,
        }
    )

    assert total == 403
    assert page_size == 20
    assert meters[0].id == "J100000"
    assert meters[0].serial_number == "SE33962"
    assert meters[0].make == "HPL"
    assert meters[0].phase == "single"
    assert meters[0].status == "Decommissioned"
    assert meters[0].dt_code == "DT-001"
    assert meters[0].network == {"transformer": "DT-001"}


def test_parse_portal_transformer_api_records():
    transformers, total, page_size = parse_portal_transformers(
        {
            "data": [
                {
                    "code": "DT-001",
                    "name": "Malviya Nagar DT 1",
                    "feederCode": "F-001",
                    "capacityKva": 100,
                }
            ],
            "total": 40,
            "page": 1,
            "pageSize": 20,
        }
    )

    assert total == 40
    assert page_size == 20
    assert transformers[0].id == "DT-001"
    assert transformers[0].label == "Malviya Nagar DT 1"
    assert transformers[0].feeder_code == "F-001"
    assert transformers[0].capacity_kva == 100


@pytest.mark.parametrize(
    "payload",
    (
        {"data": [], "total": 1, "pageSize": 0},
        {"data": [{"serialNo": "missing-id"}], "total": 1, "pageSize": 20},
        {"data": "not-a-list", "total": 1, "pageSize": 20},
    ),
)
def test_parse_portal_meter_api_rejects_invalid_records(payload):
    with pytest.raises(ValueError):
        parse_portal_meters(payload)


def test_parse_meters_normalizes_table_values():
    html = """
    <table><thead><tr><th>Meter ID</th><th>Serial Number</th><th>Status</th><th>Location</th></tr></thead>
    <tbody><tr><td> MTR-1 </td><td> SN-1 </td><td> Active </td><td> Depot A </td></tr></tbody></table>
    """
    meters = parse_meters(html, "https://example.test")
    assert meters[0].id == "MTR-1"
    assert meters[0].serial_number == "SN-1"
    assert meters[0].status == "Active"


def test_parse_meters_ignores_non_tabular_content():
    assert parse_meters("<main><p>No data discovered</p></main>", "https://example.test") == []
