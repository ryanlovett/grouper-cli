"""Tests for subject membership lookups (`grouper subject`)."""

import json
from unittest.mock import patch

import pytest

from grouper import grouper as grouper_module
from grouper.client import GrouperAPIError

from .conftest import BASE_URI

SUBJECT_ID = "1559801"

MEMBERSHIPS = {
    "WsGetMembershipsResults": {
        "resultMetadata": {"resultCode": "SUCCESS", "success": "T"},
        "wsGroups": [{"name": "test:testGroup1"}, {"name": "test:testGroup2"}],
    }
}
NO_MEMBERSHIPS = {"WsGetMembershipsResults": {"resultMetadata": {"resultCode": "SUCCESS", "success": "T"}}}


@pytest.fixture
def auth():
    return grouper_module.auth("test_user", "test_pass")


@pytest.fixture
def session_get(make_response):
    """Patch the HTTP GET the client makes; tests set its response."""
    with patch("requests.Session.get") as get:
        get.respond = lambda status, body: setattr(get, "return_value", make_response(status, body))
        yield get


class TestGetSubjectMemberships:
    def test_success(self, auth, session_get):
        session_get.respond(200, MEMBERSHIPS)
        assert grouper_module.get_subject_memberships(BASE_URI, auth, SUBJECT_ID) == [
            "test:testGroup1",
            "test:testGroup2",
        ]
        session_get.assert_called_once()
        assert session_get.call_args.args[0] == f"{BASE_URI}/subjects/{SUBJECT_ID}/memberships"

    def test_no_memberships(self, auth, session_get):
        session_get.respond(200, NO_MEMBERSHIPS)
        assert grouper_module.get_subject_memberships(BASE_URI, auth, SUBJECT_ID) == []

    def test_problem_in_response(self, auth, session_get):
        session_get.respond(200, {"WsRestResultProblem": {"resultMetadata": {"resultMessage": "Subject not found"}}})
        with pytest.raises(GrouperAPIError, match="API_PROBLEM: Subject not found"):
            grouper_module.get_subject_memberships(BASE_URI, auth, "invalid_subject")

    def test_http_error(self, auth, session_get):
        body = {"WsGetMembershipsResults": {"resultMetadata": {"resultCode": "SUBJECT_NOT_FOUND", "resultMessage": "no such subject"}}}
        session_get.respond(404, body)
        with pytest.raises(GrouperAPIError) as info:
            grouper_module.get_subject_memberships(BASE_URI, auth, "invalid_subject")
        assert info.value.code == "SUBJECT_NOT_FOUND"

    @pytest.mark.parametrize("subject_id", ["1559801", "12345", "user.name"])
    def test_subject_id_in_url(self, auth, session_get, subject_id):
        session_get.respond(200, NO_MEMBERSHIPS)
        assert grouper_module.get_subject_memberships(BASE_URI, auth, subject_id) == []
        assert session_get.call_args.args[0].endswith(f"/subjects/{subject_id}/memberships")


class TestGetSubjectInfo:
    def test_structure(self, auth):
        with patch.object(grouper_module, "get_subject_memberships", return_value=["g1", "g2", "g3"]) as memberships:
            result = grouper_module.get_subject_info(BASE_URI, auth, SUBJECT_ID)
        assert result == {"subject_id": SUBJECT_ID, "group_memberships": ["g1", "g2", "g3"], "membership_count": 3}
        memberships.assert_called_once_with(BASE_URI, auth, SUBJECT_ID)

    def test_json_serializable(self, auth):
        with patch.object(grouper_module, "get_subject_memberships", return_value=["g1"]):
            result = grouper_module.get_subject_info(BASE_URI, auth, SUBJECT_ID)
        assert json.loads(json.dumps(result)) == result

    def test_propagates_errors(self, auth):
        with patch.object(grouper_module, "get_subject_memberships", side_effect=Exception("API Error")):
            with pytest.raises(Exception, match="API Error"):
                grouper_module.get_subject_info(BASE_URI, auth, SUBJECT_ID)
