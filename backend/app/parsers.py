from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.models import HierarchyNode, Meter


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
