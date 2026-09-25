import json

import pytest
import requests

BASE_URI = "https://grouper.example.edu/gws/servicesRest/json/v2_2_100"


@pytest.fixture
def make_response():
    """Build a real requests.Response, so raise_for_status() and json() behave."""

    def _make(status, body):
        response = requests.Response()
        response.status_code = status
        response.url = BASE_URI
        response._content = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        return response

    return _make


@pytest.fixture
def clean_grouper_env(monkeypatch):
    """No Grouper credentials in the environment, whatever the developer has set."""
    for key in ("GROUPER_USER", "GROUPER_PASS", "grouper_user", "grouper_pass"):
        monkeypatch.delenv(key, raising=False)
    return monkeypatch
