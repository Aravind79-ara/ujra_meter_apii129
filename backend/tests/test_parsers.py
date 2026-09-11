from app.parsers import parse_meters


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
