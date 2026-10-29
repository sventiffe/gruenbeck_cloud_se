"""Diagnostics support for Grünbeck Cloud SE Series."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import API_BASE_URL, API_VERSION, CONF_DEVICE_ID, DOMAIN
from .coordinator import GruenbeckDataUpdateCoordinator

TO_REDACT = {
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_DEVICE_ID,
    "id",
    "serialNumber",
    "sncu",
    "name",
    "pname",
    "ptelnr",
    "pmailadress",
}

# Read-only endpoints that might hold more data (e.g. regeneration history).
# Only requested when diagnostics are downloaded.
PROBE_ENDPOINTS = [
    "/measurements",
    "/measurements/regeneration",
    "/measurements/regenerations",
    "/regenerations",
    "/history",
    "/statistics",
    "/events",
    "/notifications",
    # Leakage guard
    "/leakage",
    "/leakageguard",
    "/leakage-guard",
    "/leakageprotection",
    "/accessories",
    "/settings",
    "/status",
    "/messages",
]


async def _async_probe(coordinator: GruenbeckDataUpdateCoordinator) -> dict[str, Any]:
    """Request the probe endpoints and return status and a short body."""
    results: dict[str, Any] = {}
    try:
        token = await coordinator.api._get_web_access_token()
    except Exception as err:  # noqa: BLE001
        return {"error": str(err)}
    headers = coordinator._headers(token)
    for endpoint in PROBE_ENDPOINTS:
        url = f"{API_BASE_URL}/{coordinator.device_id}{endpoint}?api-version={API_VERSION}"
        try:
            async with coordinator.api.session.get(url, headers=headers) as resp:
                body: Any = await resp.text()
                if resp.status == 200:
                    try:
                        body = await resp.json(content_type=None)
                    except ValueError:
                        body = body[:2000]
                else:
                    body = body[:300]
                results[endpoint] = {"status": resp.status, "body": body}
        except Exception as err:  # noqa: BLE001
            results[endpoint] = {"error": str(err)}
    return results


def _entities(hass: HomeAssistant, entry: ConfigEntry) -> list[dict[str, Any]]:
    """Return the registered entities with their current state."""
    result = []
    for entity in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id):
        state = hass.states.get(entity.entity_id)
        result.append(
            {
                "entity_id": entity.entity_id,
                "key": (entity.unique_id or "").removeprefix(
                    f"{entry.data[CONF_DEVICE_ID]}_"
                ),
                "translation_key": entity.translation_key,
                "disabled_by": entity.disabled_by,
                "state": state.state if state else None,
            }
        )
    return result


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics with the raw cloud responses."""
    coordinator: GruenbeckDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "data": async_redact_data(coordinator.data or {}, TO_REDACT),
        "setting_changes": coordinator.setting_changes,
        "entities": _entities(hass, entry),
        "probe": async_redact_data(await _async_probe(coordinator), TO_REDACT),
    }
