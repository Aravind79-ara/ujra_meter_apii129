from app.models import HierarchyNode, Meter


DEMO_METERS = [
    Meter(id="MTR-101", serial_number="UJM-2026-101", status="active", location="Zone A / Building 01", network={"feeder": "Feeder A", "transformer": "TX-01"}),
    Meter(id="MTR-102", serial_number="UJM-2026-102", status="active", location="Zone A / Building 02", network={"feeder": "Feeder A", "transformer": "TX-01"}),
    Meter(id="MTR-103", serial_number="UJM-2026-103", status="inactive", location="Zone B / Building 04", network={"feeder": "Feeder B", "transformer": "TX-02"}),
]


DEMO_HIERARCHY = [HierarchyNode(id="flock-energy", label="Flock Energy", kind="organization", children=[HierarchyNode(id="zone-a", label="Zone A", kind="zone", children=[HierarchyNode(id="building-01", label="Building 01", kind="building", children=[HierarchyNode(id="floor-01", label="Floor 01", kind="floor", children=[HierarchyNode(id="MTR-101", label="MTR-101", kind="meter")])])])])]
