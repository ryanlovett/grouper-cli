#!/usr/bin/python3
# vim: set et sw=4 ts=4:

# Requires Grouper API credentials.

# Grouper/CalGroups API
# https://calnetweb.berkeley.edu/calnet-technologists/calgroups-integration/calgroups-api-information

import argparse
import json
import logging
import os
import pathlib
import sys

from grouper import grouper

# We use f-strings from python >= 3.6.
assert sys.version_info >= (3, 6)

# logging
logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
logger = logging.getLogger('grouper')

secret_keys = [ 'grouper_user', 'grouper_pass' ]

def has_all_keys(d, keys):
    return all (k in d for k in keys)

def read_json_data(filename, required_keys):
    '''Read and validate data from a json file.'''
    if not os.path.exists(filename):
        raise Exception(f"No such file: {filename}")
    data = json.loads(open(filename).read())
    # check that we've got all of our required keys
    if not has_all_keys(data, required_keys):
        missing = set(required_keys) - set(data.keys())
        s = f"Missing parameters in {filename}: {missing}"
        raise Exception(s)
    return data

def read_credentials(filename, required_keys=secret_keys):
    '''Read credentials from {filename}. Returns a dict.'''
    return read_json_data(filename, required_keys)

def read_member_file(f):
    '''Given an io file, return non-empty lines as a list.''' 
    members = []
    line = f.readline()
    while line != '':
        val = line.strip()
        if val != '':
            members.append(val)
        line = f.readline()
    return members

def credentials_file():
    '''Default path to credentials file.'''
    return pathlib.PurePath.joinpath(pathlib.Path.home(), '.grouper.json')

## main
def main():
    default_creds_file = str(credentials_file())

    parser = argparse.ArgumentParser(description="Manage Grouper groups.")
    parser.add_argument('-B', dest='base_uri', help='Grouper base uri')
    parser.add_argument('-C', dest='credentials',
        default=default_creds_file, help='Credentials file')
    parser.add_argument('-v', dest='verbose', action='store_true',
        help='Be verbose')
    parser.add_argument('-d', dest='debug', action='store_true',
        help='Debug')
    
    subparsers = parser.add_subparsers(dest='command')
    
    list_parser = subparsers.add_parser('list',
        help='List group and folder members')
    list_parser.add_argument('-g', dest='group', required=True, help='Group')

    find_parser = subparsers.add_parser('find', help='Find a group')
    find_parser.add_argument('-f', dest='folder', required=True, help='Folder')
    find_parser.add_argument('-g', dest='group', required=True, help='Group')

    create_parser = subparsers.add_parser('create',
        help='Create a group or folder')
    create_parser.add_argument('-n', dest='name', required=True,
        help='Displayed name of the group or folder')
    create_group = create_parser.add_mutually_exclusive_group(required=True)
    create_group.add_argument('-g', dest='group', help='Group')
    create_group.add_argument('-f', dest='folder', help='Folder')
    create_parser.add_argument('-D', dest='description', help='Description')
    
    add_parser = subparsers.add_parser('add', help='Add group members')
    add_parser.add_argument('-r', dest='replace_existing', action='store_true',
        help='Replace existing members.')
    add_parser.add_argument('-g', dest='group', required=True, help='Group')
    add_parser.add_argument('-i', dest='input', type=argparse.FileType('r'),
        help='File with members, one per line')
    add_parser.add_argument('members', metavar='campus-uid', nargs='*',
        help='a uid or a group path id')

    delete_parser = subparsers.add_parser('delete', help='Delete group members')
    delete_parser.add_argument('-g', dest='group', required=True, help='Group')
    delete_parser.add_argument('-i', dest='input', type=argparse.FileType('r'),
        help='File with members, one per line')
    delete_parser.add_argument('members', metavar='campus-uid', nargs='*',
        help='a uid or a group path id')

    attr_parser = subparsers.add_parser('attribute',
        help='Add or remove an attribute on a group')
    attr_parser.add_argument('-g', dest='group', required=True, help='Group')
    attr_group = attr_parser.add_mutually_exclusive_group(required=True)
    attr_group.add_argument('-a', dest='attr_add', help='Add attribute.')
    attr_group.add_argument('-r', dest='attr_remove', help='Remove attribute.')
    attr_group.add_argument('-c', dest='attr_check', help='Check attribute.')

    subject_parser = subparsers.add_parser('subject',
        help='Get information about a subject (member)')
    subject_parser.add_argument('-s', dest='subject_id', required=True,
        help='Subject ID (e.g., 1559801)')
    subject_parser.add_argument('--source-id', dest='source_id', default='ldap',
        help='Source ID (default: ldap)')
    subject_parser.add_argument('-J', '--json', dest='json_output', action='store_true',
        help='Output full subject information as JSON (default: show group names only)')

    args = parser.parse_args()

    # set verbosity
    if args.verbose:
        logger.setLevel(logging.INFO)
    elif args.debug:
        logger.setLevel(logging.DEBUG)
    
    base_uri = None
    if 'GROUPER_BASE_URI' in os.environ:
        base_uri = os.environ['GROUPER_BASE_URI']
    if args.base_uri:
        base_uri = args.base_uri
    if not base_uri:
        print("Set GROUPER_BASE_URI in the environment or via -B.")
        sys.exit(1)

    # e.g. https://calgroups.berkeley.edu/gws/servicesRest/json/v2_2_100
    # read credentials from credentials file
    credspath = pathlib.PosixPath(args.credentials).expanduser()
    credentials = read_credentials(credspath)
    grouper_auth = grouper.auth(
        credentials['grouper_user'], credentials['grouper_pass']
    )
    
    # take action
    if args.command == 'list':
        try:
            members = grouper.get_members(base_uri, grouper_auth, args.group)
        except grouper.GroupNotFoundException as e:
            logger.debug(str(e))
            sys.exit(1)
        else:
            for member in members: print(member)
    elif args.command == 'create':
        if args.folder:
            out = grouper.create_stem(base_uri, grouper_auth, args.folder,
                args.name, args.description)
        elif args.group:
            out = grouper.create_group(base_uri, grouper_auth, args.group,
                args.name, args.description)
    elif args.command == 'add':
        members = set(args.members) if args.members else set()
        if args.input:
            members |= set(read_member_file(args.input))
        logger.info(members)
        grouper.add_members(base_uri, grouper_auth, args.group,
            args.replace_existing, members)
    elif args.command == 'delete':
        members = set(args.members) if args.members else set()
        if args.input:
            members |= set(read_member_file(args.input))
        logger.info(members)
        grouper.delete_members(base_uri, grouper_auth, args.group, members)
    elif args.command == 'attribute':
        if args.attr_add:
            attribute = args.attr_add
            attr_op = 'assign_attr'
            value_op = 'add_value'
            value = 'yes'
            has_attr = grouper.group_has_attr(base_uri, grouper_auth,
                args.group, attribute)
            if has_attr: return
            out = grouper.assign_attribute(base_uri, grouper_auth, args.group,
                    attribute, attr_op, value_op, value)
        elif args.attr_remove:
            attribute = args.attr_remove
            attr_op = 'remove_attr'
            value_op = 'remove_value'
            value = 'no'
            has_attr = grouper.group_has_attr(base_uri, grouper_auth,
                args.group, attribute)
            if not has_attr: return
            out = grouper.assign_attribute(base_uri, grouper_auth, args.group,
                    attribute, attr_op, value_op, value)
        elif args.attr_check:
            attribute = args.attr_check
            out = grouper.group_has_attr(base_uri, grouper_auth, args.group,
                attribute)
            print(out)
    elif args.command == 'subject':
        try:
            if args.json_output:
                # Get full subject information and output as JSON
                subject_info = grouper.get_subject_info(base_uri, grouper_auth,
                    args.subject_id, args.source_id)
                print(json.dumps(subject_info, indent=2))
            else:
                # Default: just get and print the group names (one per line)
                groups = grouper.get_subject_memberships(base_uri, grouper_auth,
                    args.subject_id, args.source_id)
                for group in groups:
                    print(group)
        except Exception as e:
            logger.error(f"Error getting subject information: {e}")
            sys.exit(1)
