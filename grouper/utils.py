# vim: set et sw=4 ts=4:

import os
import json
from dotenv import load_dotenv

def has_all_keys(d, keys):
    return all(k in d for k in keys)


def read_json_data(filename, required_keys):
    """Read and validate data from a json file."""
    if not os.path.exists(filename):
        raise Exception(f"No such file: {filename}")
    data = json.loads(open(filename).read())
    if not has_all_keys(data, required_keys):
        missing = set(required_keys) - set(data.keys())
        s = f"Missing parameters in {filename}: {missing}"
        raise Exception(s)
    return data



def load_dotenv_file(filename=None):
    """Load environment variables from a .env file."""
    if filename:
        if not os.path.exists(filename):
            raise Exception(f"No such file: {filename}")
        load_dotenv(filename)
    else:
        if os.path.exists(".env"):
            load_dotenv(".env")

def read_grouper_credentials():
    """Read Grouper credentials from environment variables."""
    grouper_user = os.getenv("GROUPER_USER") or os.getenv("grouper_user")
    grouper_pass = os.getenv("GROUPER_PASS") or os.getenv("grouper_pass")
    if not grouper_user:
        raise Exception("Missing GROUPER_USER/grouper_user in environment")
    if not grouper_pass:
        raise Exception("Missing GROUPER_PASS/grouper_pass in environment")
    return {"grouper_user": grouper_user, "grouper_pass": grouper_pass}


def read_credentials(filename, required_keys):
    """Read credentials from {filename}. Returns a dict."""
    return read_json_data(filename, required_keys)


def read_member_file(f):
    """Given an io file, return non-empty lines as a list."""
    members = []
    line = f.readline()
    while line != "":
        val = line.strip()
        if val != "":
            members.append(val)
        line = f.readline()
    return members
