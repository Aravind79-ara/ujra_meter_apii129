from datetime import datetime, timedelta, timezone

from app.models import Consumption, HierarchyNode, Meter, Reading


DEMO_METERS = [
    Meter(id="MTR-101", serial_number="UJM-2026-101", status="active", location="Zone A / Building 01", network={"feeder": "Feeder A", "transformer": "TX-01"}),
    Meter(id="MTR-102", serial_number="UJM-2026-102", status="active", location="Zone A / Building 02", network={"feeder": "Feeder A", "transformer": "TX-01"}),
    Meter(id="MTR-103", serial_number="UJM-2026-103", status="inactive", location="Zone B / Building 04", network={"feeder": "Feeder B", "transformer": "TX-02"}),
]


def demo_consumption(meter_id: str) -> Consumption:
    values = {"MTR-101": [8, 12, 16, 10, 21, 15, 13], "MTR-102": [12, 18, 14, 20, 17, 11, 16], "MTR-103": [0, 0, 0, 0, 0, 0, 0]}
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return Consumption(meter_id=meter_id, unit="kWh", readings=[Reading(timestamp=start + timedelta(days=index), value=value) for index, value in enumerate(values.get(meter_id, []))])


DEMO_HIERARCHY = [HierarchyNode(id="flock-energy", label="Flock Energy", kind="organization", children=[HierarchyNode(id="zone-a", label="Zone A", kind="zone", children=[HierarchyNode(id="building-01", label="Building 01", kind="building", children=[HierarchyNode(id="floor-01", label="Floor 01", kind="floor", children=[HierarchyNode(id="MTR-101", label="MTR-101", kind="meter")])])])])]
