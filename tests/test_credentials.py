"""Tests for credential loading: legacy JSON files, .env files, and the environment."""

import json
from unittest.mock import patch

import pytest

from grouper import __main__ as cli
from grouper.utils import load_dotenv_file, read_credentials, read_grouper_credentials


@pytest.fixture
def json_file(tmp_path):
    path = tmp_path / "creds.json"
    path.write_text(json.dumps({"grouper_user": "json_user", "grouper_pass": "json_pass"}))
    return path


@pytest.fixture
def env_file(tmp_path):
    path = tmp_path / "test.env"
    path.write_text("GROUPER_USER=env_user\nGROUPER_PASS=env_pass\n")
    return path


class TestJSONCredentials:
    def test_default_keys(self, json_file):
        assert read_credentials(json_file) == {"grouper_user": "json_user", "grouper_pass": "json_pass"}

    def test_missing_key(self, tmp_path):
        path = tmp_path / "creds.json"
        path.write_text(json.dumps({"grouper_user": "u"}))
        with pytest.raises(Exception, match="Missing parameters"):
            read_credentials(path)

    def test_missing_file(self, tmp_path):
        with pytest.raises(Exception, match="No such file"):
            read_credentials(tmp_path / "nope.json")


class TestEnvironmentCredentials:
    def test_env_file(self, clean_grouper_env, env_file):
        load_dotenv_file(env_file)
        assert read_grouper_credentials() == {"grouper_user": "env_user", "grouper_pass": "env_pass"}

    def test_environment_variables(self, clean_grouper_env):
        clean_grouper_env.setenv("GROUPER_USER", "direct_user")
        clean_grouper_env.setenv("GROUPER_PASS", "direct_pass")
        assert read_grouper_credentials() == {"grouper_user": "direct_user", "grouper_pass": "direct_pass"}

    def test_lowercase_names(self, clean_grouper_env):
        clean_grouper_env.setenv("grouper_user", "lower_user")
        clean_grouper_env.setenv("grouper_pass", "lower_pass")
        assert read_grouper_credentials() == {"grouper_user": "lower_user", "grouper_pass": "lower_pass"}

    def test_missing(self, clean_grouper_env):
        with pytest.raises(Exception, match="Missing GROUPER_USER"):
            read_grouper_credentials()

    def test_missing_env_file(self, tmp_path):
        with pytest.raises(Exception, match="No such file"):
            load_dotenv_file(tmp_path / "nope.env")


class TestCommandLine:
    def test_json_credentials_option(self, clean_grouper_env, json_file, tmp_path, monkeypatch):
        """`grouper -C creds.json ...` passes the file's credentials to Grouper."""
        monkeypatch.chdir(tmp_path)  # keep any developer .env out of it
        argv = ["grouper", "-C", str(json_file), "-B", "https://grouper.example.edu", "list", "-g", "a:b"]
        with patch("sys.argv", argv), patch.object(cli.grouper, "get_members", return_value=["123"]) as get_members:
            cli.main()
        auth = get_members.call_args.args[1]
        assert (auth.username, auth.password) == ("json_user", "json_pass")
