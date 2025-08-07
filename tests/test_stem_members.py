#!/usr/bin/env python3
"""
Tests for the stem members functionality in grouper-cli.
Uses pytest for testing framework.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the grouper module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from grouper import grouper as grouper_module
from grouper.client import GrouperClient, GrouperException, GroupNotFoundException


class TestStemMembersFunctionality:
    """Test class for stem members functionality."""
    
    @pytest.fixture
    def mock_auth(self):
        """Fixture to provide mock authentication."""
        return grouper_module.auth('test_user', 'test_pass')
    
    @pytest.fixture
    def base_uri(self):
        """Fixture to provide base URI."""
        return 'https://test.grouper.edu/gws/servicesRest/json/v2_5_000'
    
    @pytest.fixture
    def test_stem(self):
        """Fixture to provide test stem name."""
        return 'test:stem'
    
    @pytest.fixture
    def mock_groups_response(self):
        """Fixture for a successful groups API response."""
        return {
            "WsFindGroupsResults": {
                "responseMetadata": {
                    "millis": "49",
                    "serverVersion": "2.5.0"
                },
                "resultMetadata": {
                    "resultCode": "SUCCESS",
                    "resultMessage": "Found 2 groups",
                    "success": "T"
                },
                "groupResults": [
                    {
                        "displayExtension": "testGroup1",
                        "displayName": "test:stem:testGroup1",
                        "description": "Test Group 1",
                        "extension": "testGroup1",
                        "name": "test:stem:testGroup1"
                    },
                    {
                        "displayExtension": "testGroup2",
                        "displayName": "test:stem:testGroup2",
                        "description": "Test Group 2",
                        "extension": "testGroup2",
                        "name": "test:stem:testGroup2"
                    }
                ]
            }
        }
    
    @pytest.fixture
    def mock_stems_response(self):
        """Fixture for a successful stems API response."""
        return {
            "WsFindStemsResults": {
                "responseMetadata": {
                    "millis": "35",
                    "serverVersion": "2.5.0"
                },
                "resultMetadata": {
                    "resultCode": "SUCCESS",
                    "resultMessage": "Found 1 stem",
                    "success": "T"
                },
                "stemResults": [
                    {
                        "wsStem": {
                            "displayExtension": "subStem",
                            "displayName": "test:stem:subStem",
                            "description": "Sub Stem",
                            "extension": "subStem",
                            "name": "test:stem:subStem"
                        }
                    }
                ]
            }
        }
    
    def test_get_stem_members_groups_only(self, mock_auth, base_uri, test_stem, mock_groups_response):
        """Test getting stem members - groups only."""
        with patch.object(GrouperClient, '_make_request') as mock_request:
            mock_request.return_value = mock_groups_response
            
            client = GrouperClient(base_uri, mock_auth)
            result = client.get_stem_members(test_stem, "ONE", "groups")
            
            # Verify results
            assert "groups" in result
            assert "stems" in result
            assert len(result["groups"]) == 2
            assert len(result["stems"]) == 0
            
            # Check group details
            assert result["groups"][0]["name"] == "test:stem:testGroup1"
            assert result["groups"][0]["displayName"] == "test:stem:testGroup1"
            assert result["groups"][0]["description"] == "Test Group 1"
            assert result["groups"][1]["name"] == "test:stem:testGroup2"
    
    def test_get_stem_members_all_types(self, mock_auth, base_uri, test_stem, 
                                      mock_groups_response, mock_stems_response):
        """Test getting stem members - both groups and stems."""
        with patch.object(GrouperClient, '_make_request') as mock_request:
            mock_request.side_effect = [mock_groups_response, mock_stems_response]
            
            client = GrouperClient(base_uri, mock_auth)
            result = client.get_stem_members(test_stem, "ONE", "all")
            
            # Verify results
            assert len(result["groups"]) == 2
            assert len(result["stems"]) == 1
            
            # Check stem details
            assert result["stems"][0]["name"] == "test:stem:subStem"
            assert result["stems"][0]["displayName"] == "test:stem:subStem"
            assert result["stems"][0]["description"] == "Sub Stem"
    
    def test_get_stem_members_empty_response(self, mock_auth, base_uri, test_stem):
        """Test handling of empty stem members response."""
        empty_response = {
            "WsFindGroupsResults": {
                "responseMetadata": {
                    "millis": "28",
                    "serverVersion": "2.5.0"
                },
                "resultMetadata": {
                    "resultCode": "SUCCESS",
                    "resultMessage": "Found 0 groups",
                    "success": "T"
                }
            }
        }
        
        with patch.object(GrouperClient, '_make_request') as mock_request:
            mock_request.return_value = empty_response
            
            client = GrouperClient(base_uri, mock_auth)
            result = client.get_stem_members(test_stem, "ONE", "groups")
            
            assert result["groups"] == []
            assert result["stems"] == []
    
    def test_get_stem_members_stems_error_handling(self, mock_auth, base_uri, test_stem, 
                                                  mock_groups_response):
        """Test that stem errors don't break the whole operation."""
        with patch.object(GrouperClient, '_make_request') as mock_request:
            # First call (groups) succeeds, second call (stems) fails
            mock_request.side_effect = [mock_groups_response, GrouperException("Stem error")]
            
            client = GrouperClient(base_uri, mock_auth)
            result = client.get_stem_members(test_stem, "ONE", "all")
            
            # Should still return groups even if stems fail
            assert len(result["groups"]) == 2
            assert len(result["stems"]) == 0
    
    def test_get_stem_members_legacy_function(self, mock_auth, base_uri, test_stem):
        """Test the legacy wrapper function."""
        with patch.object(GrouperClient, 'get_stem_members') as mock_method:
            expected_result = {"groups": [], "stems": []}
            mock_method.return_value = expected_result
            
            result = grouper_module.get_stem_members(base_uri, mock_auth, test_stem)
            
            assert result == expected_result
            mock_method.assert_called_once_with(test_stem, "ONE", "all")
    
    def test_get_stem_members_with_custom_parameters(self, mock_auth, base_uri, test_stem):
        """Test the legacy function with custom parameters."""
        with patch.object(GrouperClient, 'get_stem_members') as mock_method:
            expected_result = {"groups": [], "stems": []}
            mock_method.return_value = expected_result
            
            result = grouper_module.get_stem_members(
                base_uri, mock_auth, test_stem, scope="SUB", subject_types="stems"
            )
            
            assert result == expected_result
            mock_method.assert_called_once_with(test_stem, "SUB", "stems")


class TestStemMembersParameterValidation:
    """Test parameter validation for stem members functions."""
    
    @pytest.mark.parametrize("stem,scope,subject_types", [
        ("test:stem", "ONE", "all"),
        ("test:parent:child", "SUB", "groups"),
        ("root", "ONE", "stems"),
    ])
    def test_valid_parameters(self, stem, scope, subject_types):
        """Test that valid parameters are accepted."""
        with patch.object(GrouperClient, '_make_request') as mock_request:
            mock_response = {
                "WsFindGroupsResults": {
                    "resultMetadata": {"resultCode": "SUCCESS", "success": "T"}
                }
            }
            mock_request.return_value = mock_response
            
            auth = grouper_module.auth('test_user', 'test_pass')
            base_uri = 'https://test.grouper.edu/gws/servicesRest/json/v2_5_000'
            
            # Should not raise an exception
            result = grouper_module.get_stem_members(base_uri, auth, stem, scope, subject_types)
            assert isinstance(result, dict)
            assert "groups" in result
            assert "stems" in result


class TestStemMembersIntegration:
    """Integration tests for stem members functionality."""
    
    def test_stem_members_response_structure(self):
        """Test that stem members response has correct structure."""
        with patch.object(GrouperClient, '_make_request') as mock_request:
            mock_response = {
                "WsFindGroupsResults": {
                    "resultMetadata": {"resultCode": "SUCCESS", "success": "T"},
                    "groupResults": [
                        {
                            "name": "test:group",
                            "displayName": "Test Group",
                            "description": "A test group",
                            "extension": "group",
                            "displayExtension": "group"
                        }
                    ]
                }
            }
            mock_request.return_value = mock_response
            
            auth = grouper_module.auth('test_user', 'test_pass')
            base_uri = 'https://test.grouper.edu/gws/servicesRest/json/v2_5_000'
            
            result = grouper_module.get_stem_members(base_uri, auth, "test:stem")
            
            # Verify structure
            assert isinstance(result, dict)
            assert "groups" in result
            assert "stems" in result
            assert isinstance(result["groups"], list)
            assert isinstance(result["stems"], list)
            
            # Verify group structure if present
            if result["groups"]:
                group = result["groups"][0]
                expected_keys = ["name", "displayName", "description", "extension", "displayExtension"]
                for key in expected_keys:
                    assert key in group


if __name__ == "__main__":
    # Allow running pytest from this file directly
    pytest.main([__file__])
