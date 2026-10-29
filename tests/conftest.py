"""Fixtures for the Grünbeck Cloud SE tests.

The cloud is replaced by a fake aiohttp session that answers with recorded
responses of a softliQ SE21 (anonymized).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Import the integration so that it can be patched
import custom_components.gruenbeck_cloud_se  # noqa: F401

DOMAIN = "gruenbeck_cloud_se"
DEVICE_ID = "softliQ.SE/TEST"
FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "softliq_se21.json").read_text()
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable the custom integration in all tests."""
    yield


class FakeResponse:
    """Minimal aiohttp response."""

    def __init__(self, data: Any, status: int = 200) -> None:
        self.data, self.status = data, status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def json(self, content_type=None):
        return self.data

    async def text(self):
        return json.dumps(self.data) if not isinstance(self.data, str) else self.data


class FakeCloud:
    """Fake Grünbeck cloud with one device."""

    closed = False

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.calls: list[tuple] = []

    def _path(self, url: str) -> str:
        return url.split(DEVICE_ID, 1)[1].split("?", 1)[0]

    def get(self, url, headers=None):
        path = self._path(url)
        self.calls.append(("GET", path))
        answers = {
            "": self.data["info"],
            "/parameters": self.data["parameters"],
            "/measurements/water": self.data["water"],
            "/measurements/salt": self.data["salt"],
            "/update": self.data["update"],
        }
        if path in answers:
            return FakeResponse(copy.deepcopy(answers[path]))
        return FakeResponse("", 404)

    def post(self, url, headers=None, json=None):
        self.calls.append(("POST", self._path(url)))
        return FakeResponse({})

    def request(self, method, url, headers=None, json=None):
        self.calls.append((method, self._path(url), json))
        if method == "PATCH":
            self.data["parameters"].update(json)
            return FakeResponse({**self.data["parameters"], "$pending": list(json)})
        return FakeResponse("", 404)


@pytest.fixture
def cloud_data() -> dict[str, Any]:
    """Return a fresh copy of the recorded cloud data."""
    return copy.deepcopy(FIXTURE)


@pytest.fixture
def cloud(cloud_data) -> FakeCloud:
    """Return the fake cloud."""
    return FakeCloud(cloud_data)


@pytest.fixture
async def setup_integration(hass, cloud):
    """Set up the integration against the fake cloud."""

    async def _setup(language: str = "en", before=None) -> MockConfigEntry:
        hass.config.language = language
        api = MagicMock()
        api.login = AsyncMock()
        api.close = AsyncMock()
        api._get_web_access_token = AsyncMock(return_value="token")
        api.session = cloud
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"username": "user", "password": "pass", "device_id": DEVICE_ID},
        )
        entry.add_to_hass(hass)
        if before is not None:
            before(entry)
        with patch(f"custom_components.{DOMAIN}.PyGruenbeckCloud", return_value=api):
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()
        return entry

    return _setup
