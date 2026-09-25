"""Tests for how GrouperClient reports Grouper failures."""

from unittest.mock import patch

import pytest
import requests

from grouper import grouper as grouper_module
from grouper.client import (
    GroupNotFoundException,
    GrouperAPIError,
    GrouperClient,
    GrouperException,
)

from .conftest import BASE_URI


def result(key, code, message="details", success=None):
    meta = {"resultCode": code, "resultMessage": message}
    if success is not None:
        meta["success"] = success
    return {key: {"resultMetadata": meta}}


@pytest.fixture
def client():
    return GrouperClient(BASE_URI, requests.auth.HTTPBasicAuth("u", "p"))


class TestHTTPErrorBodies:
    """Grouper puts the real reason for an HTTP error in the JSON body."""

    def test_group_not_found(self, client, make_response):
        body = result("WsGetMembersLiteResult", "GROUP_NOT_FOUND", "no such group")
        with patch.object(client.session, "get", return_value=make_response(404, body)):
            with pytest.raises(GroupNotFoundException, match="no such group") as info:
                client.get_members("a:b")
        assert isinstance(info.value.__cause__, requests.exceptions.HTTPError)

    def test_other_result_codes(self, client, make_response):
        body = result("WsAddMemberResults", "INSUFFICIENT_PRIVILEGES", "not allowed")
        with patch.object(client.session, "put", return_value=make_response(500, body)):
            with pytest.raises(GrouperAPIError) as info:
                client.add_members("a:b", ["123"])
        assert info.value.code == "INSUFFICIENT_PRIVILEGES"
        assert info.value.message == "not allowed"
        assert info.value.response_data == body

    def test_rest_result_problem(self, client, make_response):
        body = {"WsRestResultProblem": {"resultMetadata": {"resultMessage": "bad request"}}}
        with patch.object(client.session, "post", return_value=make_response(400, body)):
            with pytest.raises(GrouperAPIError, match="API_PROBLEM: bad request"):
                client.find_group("a", "b")

    def test_non_json_error_body(self, client, make_response):
        with patch.object(client.session, "get", return_value=make_response(401, "<html>Unauthorized</html>")):
            with pytest.raises(GrouperException, match="HTTP request failed: 401") as info:
                client.get_members("a:b")
        assert not isinstance(info.value, GrouperAPIError)

    def test_legacy_function_raises_group_not_found(self, make_response):
        """`grouper list -g <missing group>` relies on this to exit cleanly."""
        body = result("WsGetMembersLiteResult", "GROUP_NOT_FOUND")
        with patch("requests.Session.get", return_value=make_response(404, body)):
            with pytest.raises(GroupNotFoundException):
                grouper_module.get_members(BASE_URI, grouper_module.auth("u", "p"), "a:b")


class TestMembershipWrites:
    """add_members/delete_members check the result, as the legacy functions do."""

    @pytest.mark.parametrize("method, key", [
        ("add_members", "WsAddMemberResults"),
        ("delete_members", "WsDeleteMemberResults"),
    ])
    def test_failure_reported_with_http_200(self, client, make_response, method, key):
        body = result(key, "PROBLEM_WITH_ASSIGNMENT", "subject not found", success="F")
        with patch.object(client.session, "put", return_value=make_response(200, body)):
            with pytest.raises(GrouperAPIError) as info:
                getattr(client, method)("a:b", ["123"])
        assert info.value.code == "PROBLEM_WITH_ASSIGNMENT"

    @pytest.mark.parametrize("method, key", [
        ("add_members", "WsAddMemberResults"),
        ("delete_members", "WsDeleteMemberResults"),
    ])
    def test_success_returns_response(self, client, make_response, method, key):
        body = result(key, "SUCCESS", success="T")
        with patch.object(client.session, "put", return_value=make_response(200, body)):
            assert getattr(client, method)("a:b", ["123"]) == body
