from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.models import HierarchyNode, Meter


def _portal_page(payload: object) -> tuple[list[object], int, int]:
    if not isinstance(payload, dict):
        raise ValueError("Portal data must be a JSON object.")

    data = payload.get("data")
    total = payload.get("total")
    page_size = payload.get("pageSize")
    if (
        not isinstance(data, list)
        or not isinstance(total, int)
        or isinstance(total, bool)
        or not isinstance(page_size, int)
        or isinstance(page_size, bool)
        or page_size < 1
    ):
        raise ValueError("Portal data has an unexpected page format.")

    return data, total, page_size


def parse_portal_meters(payload: object) -> tuple[list[Meter], int, int]:
    records, total, page_size = _portal_page(payload)
    meters: list[Meter] = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Portal meter data contains an invalid record.")

        meter_id = record.get("meterId")
        if not isinstance(meter_id, str) or not meter_id:
            raise ValueError("Portal meter data is missing a meter ID.")

        serial_number = record.get("serialNo")
        make = record.get("make")
        phase = record.get("phaseType")
        status = record.get("installStatus")
        dt_code = record.get("dtCode")
        optional_values = (serial_number, make, phase, status, dt_code)
        if any(value is not None and not isinstance(value, str) for value in optional_values):
            raise ValueError("Portal meter data contains an invalid field.")

        meters.append(
            Meter(
                id=meter_id,
                serial_number=serial_number,
                make=make,
                phase=phase,
                status=status,
                dt_code=dt_code,
                network={"transformer": dt_code} if dt_code else {},
            )
        )

    return meters, total, page_size


def parse_portal_transformers(
    payload: object,
) -> tuple[list[HierarchyNode], int, int]:
    records, total, page_size = _portal_page(payload)
    transformers: list[HierarchyNode] = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Portal transformer data contains an invalid record.")

        code = record.get("code")
        name = record.get("name")
        feeder_code = record.get("feederCode")
        capacity_kva = record.get("capacityKva")
        if (
            not isinstance(code, str)
            or not code
            or not isinstance(name, str)
            or not name
            or (feeder_code is not None and not isinstance(feeder_code, str))
            or (
                capacity_kva is not None
                and (
                    not isinstance(capacity_kva, int)
                    or isinstance(capacity_kva, bool)
                )
            )
        ):
            raise ValueError("Portal transformer data contains an invalid record.")

        transformers.append(
            HierarchyNode(
                id=code,
                label=name,
                kind="transformer",
                feeder_code=feeder_code,
                capacity_kva=capacity_kva,
            )
        )

    return transformers, total, page_size


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = " ".join(value.split())
    return value or None


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def parse_meters(html: str, base_url: str) -> list[Meter]:
    soup = BeautifulSoup(html, "html.parser")
    meters: list[Meter] = []
    for table in soup.find_all("table"):
        headers = [_key(cell.get_text(" ", strip=True)) for cell in table.find_all("th")]
        if not headers:
            continue
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells or len(cells) != len(headers):
                continue
            values = {headers[index]: _clean(cell.get_text(" ", strip=True)) for index, cell in enumerate(cells)}
            link = row.find("a", href=True)
            identifier = values.get("id") or values.get("meter_id") or values.get("meter")
            if not identifier and link:
                identifier = _clean(link.get_text(" ", strip=True))
            if not identifier:
                continue
            meters.append(Meter(
                id=identifier,
                serial_number=values.get("serial_number") or values.get("serial") or values.get("meter_serial_number"),
                status=values.get("status") or values.get("state"),
                location=values.get("location") or values.get("address"),
                network={key: values.get(key) for key in ("feeder", "transformer", "substation", "network") if values.get(key)},
                source_url=urljoin(base_url, link["href"]) if link else None,
            ))
    return meters


def parse_hierarchy(html: str) -> list[HierarchyNode]:
    soup = BeautifulSoup(html, "html.parser")
    roots: list[HierarchyNode] = []
    for table in soup.find_all("table"):
        headers = [_key(cell.get_text(" ", strip=True)) for cell in table.find_all("th")]
        if not headers:
            continue
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells or len(cells) != len(headers):
                continue
            values = {headers[index]: _clean(cell.get_text(" ", strip=True)) for index, cell in enumerate(cells)}
            identifier = values.get("id") or values.get("transformer_id") or values.get("name")
            if identifier:
                roots.append(HierarchyNode(id=identifier, label=identifier, kind="transformer"))
    return roots
