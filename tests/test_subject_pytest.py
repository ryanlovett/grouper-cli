#!/usr/bin/env python3
"""
Tests for the subject functionality in grouper-cli.
Uses pytest for testing framework.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the grouper module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from grouper import grouper as grouper_module


class TestSubjectFunctionality:
    """Test class for subject-related functionality."""
    
    @pytest.fixture
    def mock_auth(self):
        """Fixture to provide mock authentication."""
        return grouper_module.auth('test_user', 'test_pass')
    
    @pytest.fixture
    def base_uri(self):
        """Fixture to provide base URI."""
        return 'https://test.grouper.edu/gws/servicesRest/json/v2_5_000'
    
    @pytest.fixture
    def subject_id(self):
        """Fixture to provide test subject ID."""
        return '1559801'
    
    @pytest.fixture
    def mock_successful_response(self):
        """Fixture for a successful API response."""
        return {
            "WsGetMembershipsResults": {
                "responseMetadata": {
                    "millis": "49",
                    "serverVersion": "2.5.0"
                },
                "resultMetadata": {
                    "resultCode": "SUCCESS",
                    "resultMessage": "Found 2 results involving 2 groups and 1 subjects",
                    "success": "T"
                },
                "wsGroups": [
                    {
                        "displayExtension": "testGroup1",
                        "displayName": "test:testGroup1",
                        "enabled": "T",
                        "extension": "testGroup1",
                        "idIndex": "10031",
                        "name": "test:testGroup1",
                        "typeOfGroup": "group",
                        "uuid": "6488e4e9d11d405598a420954c86fabf"
                    },
                    {
                        "displayExtension": "testGroup2",
                        "displayName": "test:testGroup2",
                        "enabled": "T",
                        "extension": "testGroup2",
                        "idIndex": "10032",
                        "name": "test:testGroup2",
                        "typeOfGroup": "group",
                        "uuid": "7599f5f0e22e516609b531065d97fbcg"
                    }
                ]
            }
        }
    
    @pytest.fixture
    def mock_error_response(self):
        """Fixture for an error API response."""
        return {
            "WsRestResultProblem": {
                "resultMetadata": {
                    "resultCode": "INVALID_QUERY",
                    "resultMessage": "Subject not found",
                    "success": "F"
                }
            }
        }
    
    def test_get_subject_memberships_success(self, mock_auth, base_uri, subject_id, mock_successful_response):
        """Test successful retrieval of subject memberships."""
        with patch('grouper.grouper.requests.get') as mock_get:
            mock_get.return_value.json.return_value = mock_successful_response
            mock_get.return_value.status_code = 200
            
            result = grouper_module.get_subject_memberships(base_uri, mock_auth, subject_id)
            
            # Verify results
            expected_groups = ['test:testGroup1', 'test:testGroup2']
            assert result == expected_groups
            
            # Verify the API was called correctly
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert f'/subjects/{subject_id}/memberships' in args[0]
            assert kwargs['auth'] == mock_auth
            assert kwargs['headers']['Content-type'] == 'text/x-json'
    
    def test_get_subject_memberships_empty_response(self, mock_auth, base_uri, subject_id):
        """Test handling of empty membership response."""
        empty_response = {
            "WsGetMembershipsResults": {
                "responseMetadata": {
                    "millis": "28",
                    "serverVersion": "2.5.0"
                },
                "resultMetadata": {
                    "resultCode": "SUCCESS",
                    "resultMessage": "Found 0 results involving 0 groups and 0 subjects",
                    "success": "T"
                }
            }
        }
        
        with patch('grouper.grouper.requests.get') as mock_get:
            mock_get.return_value.json.return_value = empty_response
            
            result = grouper_module.get_subject_memberships(base_uri, mock_auth, subject_id)
            
            assert result == []
    
    def test_get_subject_memberships_error(self, mock_auth, base_uri, mock_error_response):
        """Test error handling for subject membership retrieval."""
        with patch('grouper.grouper.requests.get') as mock_get:
            mock_get.return_value.json.return_value = mock_error_response
            
            with pytest.raises(Exception) as exc_info:
                grouper_module.get_subject_memberships(base_uri, mock_auth, 'invalid_subject')
            
            # Verify that an exception was raised with the expected error info
            assert "resultCode" in str(exc_info.value)
    
    def test_get_subject_info_success(self, mock_auth, base_uri, subject_id):
        """Test successful retrieval of subject information."""
        expected_memberships = ['test:group1', 'test:group2', 'test:group3']
        
        with patch('grouper.grouper.get_subject_memberships') as mock_get_memberships:
            mock_get_memberships.return_value = expected_memberships
            
            result = grouper_module.get_subject_info(base_uri, mock_auth, subject_id, 'ldap')
            
            expected_result = {
                'subject_id': subject_id,
                'source_id': 'ldap',
                'group_memberships': expected_memberships,
                'membership_count': 3
            }
            
            assert result == expected_result
            
            # Verify the internal function was called correctly
            mock_get_memberships.assert_called_once_with(base_uri, mock_auth, subject_id, 'ldap')
    
    def test_get_subject_info_with_default_source(self, mock_auth, base_uri, subject_id):
        """Test subject info retrieval with default source ID."""
        with patch('grouper.grouper.get_subject_memberships') as mock_get_memberships:
            mock_get_memberships.return_value = ['test:group1']
            
            result = grouper_module.get_subject_info(base_uri, mock_auth, subject_id)
            
            assert result['source_id'] == 'ldap'  # default value
            mock_get_memberships.assert_called_once_with(base_uri, mock_auth, subject_id, 'ldap')
    
    def test_get_subject_info_propagates_errors(self, mock_auth, base_uri, subject_id):
        """Test that get_subject_info properly propagates errors from get_subject_memberships."""
        with patch('grouper.grouper.get_subject_memberships') as mock_get_memberships:
            mock_get_memberships.side_effect = Exception("API Error")
            
            with pytest.raises(Exception) as exc_info:
                grouper_module.get_subject_info(base_uri, mock_auth, subject_id)
            
            assert "API Error" in str(exc_info.value)


class TestSubjectParameterValidation:
    """Test parameter validation for subject functions."""
    
    @pytest.mark.parametrize("subject_id,source_id", [
        ("1559801", "ldap"),
        ("12345", "local"),
        ("user.name", "custom"),
    ])
    def test_valid_parameters(self, subject_id, source_id):
        """Test that valid parameters are accepted."""
        with patch('grouper.grouper.requests.get') as mock_get:
            mock_response = {
                "WsGetMembershipsResults": {
                    "resultMetadata": {"resultCode": "SUCCESS", "success": "T"}
                }
            }
            mock_get.return_value.json.return_value = mock_response
            
            auth = grouper_module.auth('test_user', 'test_pass')
            base_uri = 'https://test.grouper.edu/gws/servicesRest/json/v2_5_000'
            
            # Should not raise an exception
            result = grouper_module.get_subject_memberships(base_uri, auth, subject_id, source_id)
            assert isinstance(result, list)


if __name__ == "__main__":
    # Allow running pytest from this file directly
    pytest.main([__file__])
