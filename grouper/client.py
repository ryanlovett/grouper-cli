# vim:set et ts=4 sw=4:

import json
import logging
from typing import Dict, List, Optional, Any, Union

import requests

# logging
logger = logging.getLogger("grouper")

success_codes = [
    "SUCCESS",
    "SUCCESS_INSERTED",
    "SUCCESS_NO_CHANGES_NEEDED",
    "SUCCESS_UPDATED",
]


# Custom exceptions for better error handling
class GrouperException(Exception):
    """Base exception for Grouper API errors"""

    pass


class GroupNotFoundException(GrouperException):
    """Exception raised when a group is not found"""

    pass


class GrouperAPIError(GrouperException):
    """Exception raised for API-level errors"""

    def __init__(self, code: str, message: str, response_data: Optional[Dict] = None):
        self.code = code
        self.message = message
        self.response_data = response_data
        super().__init__(f"{code}: {message}")


class GrouperClient:
    """Client for interacting with Grouper Web Services API

    This is the modern, optimized API for interacting with Grouper.
    It provides better error handling, session management, and a cleaner interface.

    Example usage:
        client = GrouperClient(base_uri, auth)
        members = client.get_members("my:group")
        client.create_group("my:new:group", "Display Name")
    """

    def __init__(self, base_uri: str, auth: requests.auth.AuthBase):
        self.base_uri = base_uri.rstrip("/")
        self.auth = auth
        self.session = requests.Session()
        self.session.auth = auth
        self.session.headers.update({"Content-type": "text/x-json"})

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict:
        """Make HTTP request and handle common error patterns"""
        url = f'{self.base_uri}/{endpoint.lstrip("/")}'

        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(
                    url, data=json.dumps(data) if data else None
                )
            elif method.upper() == "PUT":
                response = self.session.put(
                    url, data=json.dumps(data) if data else None
                )
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed: {e}")
            raise GrouperException(f"HTTP request failed: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            raise GrouperException(f"Invalid JSON response: {e}") from e

    def _check_response_errors(self, response: Dict, expected_result_key: str) -> None:
        """Check response for common error patterns and raise appropriate exceptions"""
        # Check for WsRestResultProblem
        problem_key = "WsRestResultProblem"
        if problem_key in response:
            meta = response[problem_key]["resultMetadata"]
            message = meta.get("resultMessage", "Unknown error")
            logger.error(f"{problem_key} in output: {message}")
            raise GrouperAPIError("API_PROBLEM", message, response)

        # Check for specific result errors
        if expected_result_key in response:
            result_meta = response[expected_result_key]["resultMetadata"]
            code = result_meta["resultCode"]
            message = result_meta.get("resultMessage", "Unknown error")

            if code == "GROUP_NOT_FOUND":
                raise GroupNotFoundException(message)
            elif code not in success_codes:
                raise GrouperAPIError(code, message, response)

    # High-level API methods
    def get_members(self, group: str) -> List[str]:
        """Get group members."""
        logger.debug(f"get members of {group}")
        response = self._make_request("GET", f"/groups/{group}/members")

        # Special handling for this endpoint's response structure
        if "WsRestResultProblem" in response:
            msg = response["WsRestResultProblem"]["resultMetadata"]["resultMessage"]
            raise GrouperException(msg)

        results_key = "WsGetMembersLiteResult"
        if results_key in response:
            code = response[results_key]["resultMetadata"]["resultCode"]
            if code == "GROUP_NOT_FOUND":
                msg = response[results_key]["resultMetadata"]["resultMessage"]
                raise GroupNotFoundException(msg)
            elif code not in ["SUCCESS"]:
                msg = response[results_key]["resultMetadata"]["resultMessage"]
                raise GrouperAPIError(code, msg)
            if "wsSubjects" in response[results_key]:
                return [
                    subject["id"] for subject in response[results_key]["wsSubjects"]
                ]
        return []

    def create_stem(self, stem: str, name: str, description: str = "") -> Dict:
        """Create a stem."""
        logger.info(f"creating stem {stem}")
        extension = stem.split(":")[-1]
        if not description:
            description = name

        data = {
            "WsRestStemSaveLiteRequest": {
                "stemName": stem,
                "extension": extension,
                "description": description,
                "displayExtension": name,
            }
        }
        return self._make_request("POST", f"/stems/{stem}", data)

    def create_group(self, group: str, name: str, description: str = "") -> Dict:
        """Create a group."""
        logger.info(f"creating group {group}")
        if not description:
            description = name

        data = {
            "WsRestGroupSaveLiteRequest": {
                "groupName": group,
                "description": description,
                "displayExtension": name,
            }
        }
        return self._make_request("POST", f"/groups/{group}", data)

    def create_composite_group(
        self, group: str, name: str, left_group: str, right_group: str
    ) -> Dict:
        """Create a new group as a composite of left_group and right_group."""
        logger.info(f"creating composite {group}")
        data = {
            "WsRestGroupSaveRequest": {
                "wsGroupToSaves": [
                    {
                        "wsGroup": {
                            "description": name,
                            "detail": {
                                "compositeType": "intersection",
                                "hasComposite": "T",
                                "leftGroup": {"name": left_group},
                                "rightGroup": {"name": right_group},
                            },
                            "name": group,
                        },
                        "wsGroupLookup": {"groupName": group},
                    }
                ]
            }
        }
        return self._make_request("POST", f"/groups/{group}", data)

    def delete_group(self, group: str) -> Dict:
        """Delete a group."""
        logger.info(f"deleting group {group}")
        return self._make_request("DELETE", f"/stems/{group}")

    def find_group(self, stem: str, name: str) -> Dict:
        """Find a group."""
        logger.info(f"finding group {stem}:{name}")
        data = {
            "WsRestFindGroupsLiteRequest": {
                "queryFilterType": "FIND_BY_GROUP_NAME_EXACT",
                "stemName": stem,
                "groupName": name,
            }
        }
        return self._make_request("POST", "/groups", data)

    def add_members(
        self, group: str, members: List[str], replace_existing: bool = False
    ) -> Dict:
        """Add members to a group."""
        logger.info(f"adding members to {group}")

        def boolean_string(b):
            return {True: "T", False: "F"}[b]

        data = {
            "WsRestAddMemberRequest": {
                "replaceAllExisting": boolean_string(replace_existing),
                "subjectLookups": [],
            }
        }

        for member in members:
            member_key = (
                "subjectId"
                if (isinstance(member, int) or member.isalpha())
                else "subjectIdentifier"
            )
            data["WsRestAddMemberRequest"]["subjectLookups"].append(
                {member_key: member}
            )

        return self._make_request("PUT", f"/groups/{group}/members", data)

    def delete_members(self, group: str, members: List[str]) -> Dict:
        """Delete members from a group."""
        logger.info(f"deleting members from {group}")
        data = {"WsRestDeleteMemberRequest": {"subjectLookups": []}}

        for member in members:
            member_key = (
                "subjectId"
                if (isinstance(member, int) or member.isalpha())
                else "subjectIdentifier"
            )
            data["WsRestDeleteMemberRequest"]["subjectLookups"].append(
                {member_key: member}
            )

        return self._make_request("PUT", f"/groups/{group}/members", data)

    def assign_attribute(
        self,
        group: str,
        attribute: str,
        attr_op: str,
        value_op: str = "",
        value: str = "",
    ) -> Dict:
        """Assign attribute to a group."""
        logger.info(f"assigning attributes to {group}")
        data = {
            "WsRestAssignAttributesLiteRequest": {
                "attributeAssignOperation": attr_op,
                "attributeAssignType": "group",
                "wsAttributeDefNameName": attribute,
                "wsOwnerGroupName": group,
            }
        }

        if value_op == "add_value":
            data["WsRestAssignAttributesLiteRequest"]["valueSystem"] = value
            data["WsRestAssignAttributesLiteRequest"][
                "attributeAssignValueOperation"
            ] = value_op

        return self._make_request("POST", "/attributeAssignments", data)

    def get_assign_attribute(
        self, attribute: str, group: Optional[str] = None, stem: Optional[str] = None
    ) -> Dict:
        """Get assigned attributes."""
        logger.info(f"getting attribute {attribute} from {group or stem}")
        data = {
            "WsRestGetAttributeAssignmentsLiteRequest": {
                "wsAttributeDefNameName": attribute,
                "attributeAssignType": "group",
                "includeAssignmentsOnAssignments": "F",
            }
        }

        if group is not None:
            data["WsRestGetAttributeAssignmentsLiteRequest"]["wsOwnerGroupName"] = group
        elif stem is not None:
            data["WsRestGetAttributeAssignmentsLiteRequest"]["wsOwnerStemName"] = stem

        return self._make_request("POST", "/attributeAssignments", data)

    def group_has_attr(self, group: str, attribute: str) -> bool:
        """Check if group has a specific attribute."""
        try:
            response = self.get_assign_attribute(attribute, group=group)
            groups = response["WsGetAttributeAssignmentsResults"]["wsGroups"]
            if len(groups) != 1:
                return False
            retval = groups[0]["name"] == group
            logger.info(f"{group} has {attribute}: {retval}")
            return retval
        except GrouperException:
            return False

    def get_subject_memberships(
        self, subject_id: str, source_id: str = "ldap"
    ) -> List[str]:
        """Get the groups that a subject belongs to."""
        logger.info(f"getting memberships for subject {subject_id}")
        response = self._make_request("GET", f"/subjects/{subject_id}/memberships")

        groups = []
        results_key = "WsGetMembershipsResults"
        if results_key in response and "wsGroups" in response[results_key]:
            groups = [group["name"] for group in response[results_key]["wsGroups"]]

        logger.info(f"subject {subject_id} is member of {len(groups)} groups")
        return groups

    def get_subject_info(self, subject_id: str, source_id: str = "ldap") -> Dict:
        """Get information about a subject including their group memberships."""
        logger.info(f"getting subject information for {subject_id}")

        try:
            memberships = self.get_subject_memberships(subject_id, source_id)
            return {
                "subject_id": subject_id,
                "source_id": source_id,
                "group_memberships": memberships,
                "membership_count": len(memberships),
            }
        except Exception as e:
            logger.error(f"Error getting subject info for {subject_id}: {e}")
            raise

    def get_stem_members(
        self, stem: str, scope: str = "ONE", subject_types: str = "all"
    ) -> Dict:
        """Get all groups and sub-stems within a stem (folder).

        Args:
            stem: The stem name to get members from
            scope: Search scope - "ONE" for direct children only, "SUB" for recursive
            subject_types: Types to return - "all", "groups", "stems"

        Returns:
            Dict containing groups and stems found within the stem
        """
        logger.info(f"getting members of stem {stem}")

        result = {"groups": [], "stems": []}

        # Get groups using the correct API format
        if subject_types in ["all", "groups"]:
            try:
                # Use the correct CalGroups API format for finding groups by stem
                data = {
                    "WsRestFindGroupsLiteRequest": {
                        "queryFilterType": "FIND_BY_STEM_NAME",
                        "stemName": stem,
                    }
                }

                response = self._make_request("POST", "/groups", data)

                # Handle the response
                if "WsFindGroupsResults" in response:
                    self._check_response_errors(response, "WsFindGroupsResults")

                    # Extract groups from response
                    if "groupResults" in response["WsFindGroupsResults"]:
                        for group_info in response["WsFindGroupsResults"][
                            "groupResults"
                        ]:
                            # Filter for direct children if scope is ONE
                            if scope == "ONE":
                                # Check if this is a direct child (only one more colon after the stem)
                                expected_prefix = stem + ":"
                                if (
                                    group_info.get("name", "").startswith(
                                        expected_prefix
                                    )
                                    and ":"
                                    not in group_info.get("name", "")[
                                        len(expected_prefix) :
                                    ]
                                ):
                                    result["groups"].append(
                                        {
                                            "name": group_info.get("name"),
                                            "displayName": group_info.get(
                                                "displayName"
                                            ),
                                            "description": group_info.get(
                                                "description"
                                            ),
                                            "extension": group_info.get("extension"),
                                            "displayExtension": group_info.get(
                                                "displayExtension"
                                            ),
                                        }
                                    )
                            else:
                                # SUB scope - include all matching groups
                                result["groups"].append(
                                    {
                                        "name": group_info.get("name"),
                                        "displayName": group_info.get("displayName"),
                                        "description": group_info.get("description"),
                                        "extension": group_info.get("extension"),
                                        "displayExtension": group_info.get(
                                            "displayExtension"
                                        ),
                                    }
                                )

            except GrouperException as e:
                logger.warning(f"Could not fetch groups for {stem}: {e}")

        # Get stems - this might need to be a separate call or might not be supported
        # For now, let's comment this out until we get groups working
        # if subject_types in ["all", "stems"]:
        #     logger.info(f"Stem listing not yet implemented")

        return result
