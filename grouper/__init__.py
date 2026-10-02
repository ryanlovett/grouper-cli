# vim:set et ts=4 sw=4:

"""
Grouper API Client Library

This package provides both legacy function-based API and modern class-based API
for interacting with Grouper Web Services.

Legacy API (backward compatible):
    from grouper import grouper
    members = grouper.get_members(base_uri, auth, group)

Modern API:
    from grouper.client import GrouperClient
    client = GrouperClient(base_uri, auth)
    members = client.get_members(group)

The legacy API internally uses the modern client for improved performance
and error handling while maintaining full backward compatibility.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("grouper")
except PackageNotFoundError:
    # Package is not installed, e.g. running from a source checkout
    __version__ = "unknown"
