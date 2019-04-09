# vim:set et ts=4 sw=4:

import json
import logging

import requests

# logging
logger = logging.getLogger('grouper')

class GroupNotFoundException(Exception): pass

def auth(user, password):
    return requests.auth.HTTPBasicAuth(user, password)

def get_members(base_uri, auth, group):
    '''Get group members.'''
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/getMembers/WsSampleGetMembersRestLite_json.txt
    logger.debug(f'get members of {group}')
    r = requests.get(f'{base_uri}/groups/{group}/members',
        auth=auth, headers={'Content-type':'text/x-json'}
    )
    out = r.json()
    if 'WsRestResultProblem' in out:
        msg = out['WsRestResultProblem']['resultMetadata']['resultMessage']
        raise Exception(msg)
    results_key = 'WsGetMembersLiteResult'
    if results_key in out:
        code = out[results_key]['resultMetadata']['resultCode']
        if code == 'GROUP_NOT_FOUND':
            msg = out[results_key]['resultMetadata']['resultMessage']
            raise GroupNotFoundException(msg)
        elif code not in ['SUCCESS']:
            msg = out[results_key]['resultMetadata']['resultMessage']
            raise Exception(f'{code}: {msg}')
        if 'wsSubjects' in out[results_key]: # there are members
            value = out[results_key]['wsSubjects']
            return map(lambda x: x['id'], value)
    return []

def create_stem(base_uri, auth, stem, name, description=''):
    '''Create a stem.'''
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/stemSave/WsSampleStemSaveRestLite_json.txt
    logger.info(f'creating stem {stem}')

    # the very last stem element
    extension = stem.split(':')[-1]
    # provide a minimal description
    if description == '': description = name

    data = {
        "WsRestStemSaveLiteRequest": {
            "stemName": stem,
            "extension": extension,
            "description": description,
            "displayExtension": name,
        }
    }
    r = requests.post(f'{base_uri}/stems/{stem}',
        data=json.dumps(data), auth=auth, headers={'Content-type':'text/x-json'}
    )
    out = r.json()
    if 'WsRestResultProblem' in out:
        msg = out['WsRestResultProblem']['resultMetadata']['resultMessage']
        raise Exception(msg)
    results_key = 'WsStemSaveLiteResult'
    if results_key in out:
        code = out[results_key]['resultMetadata']['resultCode']
        if code not in ['SUCCESS_INSERTED', 'SUCCESS_NO_CHANGES_NEEDED']:
            msg = out[results_key]['resultMetadata']['resultMessage']
            raise Exception(f'{code}: {msg}')
    return out

def create_group(base_uri, auth, group, name, description=''):
    '''Create a group.'''
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/groupSave/WsSampleGroupSaveRestLite_json.txt
    logger.info(f'creating group {group}')

    # the very last stem element
    extension = group.split(':')[-1]
    # provide a minimal description
    if description == '': description = name

    data = {
        "WsRestGroupSaveLiteRequest": {
            "groupName": group,
            #"extension": extension,
            "description": description,
            "displayExtension": name,
        }
    }
    r = requests.post(f'{base_uri}/groups/{group}',
        data=json.dumps(data), auth=auth, headers={'Content-type':'text/x-json'}
    )
    out = r.json()
    problem_key = 'WsRestResultProblem'
    if problem_key in out:
        logger.error(f'{problem_key} in output')
        meta = out[problem_key]['resultMetadata']
        raise Exception(meta)
    results_key = 'WsGroupSaveLiteResult'
    if results_key in out:
        code = out[results_key]['resultMetadata']['resultCode']
        if code not in ['SUCCESS_INSERTED', 'SUCCESS_NO_CHANGES_NEEDED']:
            msg = out[results_key]['resultMetadata']['resultMessage']
            logger.error(f'Error creating group: {group} {data}')
            raise Exception(f'{code}: {msg}')
    return out

def create_composite_group(auth, group, name, left_group, right_group):
    '''Create a new group as a composite of {left_group} and {right_group}.'''
    logger.info(f'creating composite {group}')
    data = {
        "WsRestGroupSaveRequest": {
            "wsGroupToSaves":[{
                "wsGroup":{
                   "description":name,
                   "detail":{
                        "compositeType":"intersection",
                        "hasComposite":"T",
                        "leftGroup": { "name":left_group  },
                        "rightGroup":{ "name":right_group }
                   },
                   "name":group
                },
                "wsGroupLookup":{ "groupName":group }
            }]
        }
    }
    r = requests.post(f'{base_uri}/groups/{group}', data=json.dumps(data),
        auth=auth, headers={'Content-type':'text/x-json'}
    )
    out = r.json()
    problem_key = 'WsRestResultProblem'
    if problem_key in out:
        logger.error(f'{problem_key} in output')
        meta = out[problem_key]['resultMetadata']
        raise Exception(meta)
    results_key = 'WsGroupSaveLiteResult'
    success_codes = ['SUCCESS_INSERTED', 'SUCCESS_NO_CHANGES_NEEDED']
    if results_key in out:
        code = out[results_key]['resultMetadata']['resultCode']
        if code not in success_codes:
            msg = out[results_key]['resultMetadata']['resultMessage']
            raise Exception(f'{code}: {msg}')
    return out

def find_group(base_uri, auth, stem, name):
    '''Create a group.'''
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/groupSave/WsSampleGroupSaveRestLite_json.txt
    logger.info(f'finding group {stem}:{name}')

    data = {
        "WsRestFindGroupsLiteRequest": {
            "queryFilterType": "FIND_BY_GROUP_NAME_EXACT",
            "stemName": stem,
            "groupName": name,
        }
    }
    r = requests.post(f'{base_uri}/groups',
        data=json.dumps(data), auth=auth, headers={'Content-type':'text/x-json'}
    )
    out = r.json()
    print(out)
    problem_key = 'WsRestResultProblem'
    if problem_key in out:
        logger.error(f'{problem_key} in output')
        meta = out[problem_key]['resultMetadata']
        raise Exception(meta)
    results_key = 'WsFindGroupsResults'
    if results_key in out:
        code = out[results_key]['resultMetadata']['resultCode']
        if code not in ['SUCCESS_INSERTED', 'SUCCESS_NO_CHANGES_NEEDED']:
            msg = out[results_key]['resultMetadata']['resultMessage']
            logger.error(f'Error creating group: {group} {data}')
            raise Exception(f'{code}: {msg}')
    return out

def replace_members(base_uri, auth, group, members):
    '''Replace the members of the grouper group {group} with {users}.'''
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/addMember/WsSampleAddMemberRest_json.txt
    logger.info(f'replacing members of {group}')
    data = {
        "WsRestAddMemberRequest": {
            "replaceAllExisting":"T",
            "subjectLookups":[]
        }
    }
    for member in members:
        if type(member) == int or member.isalpha():
            # UUID
            member_key = 'subjectId'
        else:
            # e.g. group path id
            member_key = 'subjectIdentifier'
        data['WsRestAddMemberRequest']['subjectLookups'].append(
            {member_key:member}
        )
    r = requests.put(f'{base_uri}/groups/{group}/members',
        data=json.dumps(data), auth=auth, headers={'Content-type':'text/x-json'}
    )
    out = r.json()
    problem_key = 'WsRestResultProblem'
    if problem_key in out:
        logger.error(f'{problem_key} in output')
        meta = out[problem_key]['resultMetadata']
        raise Exception(meta)
    results_key = 'WsAddMemberResults'
    success_codes = ['SUCCESS']
    if results_key in out:
        code = out[results_key]['resultMetadata']['resultCode']
        if code not in success_codes:
            msg = out[results_key]['resultMetadata']['resultMessage']
            raise Exception(f'{code}: {msg}')
    return out

def assign_attribute(base_uri, auth, group, attribute, operation):
    '''Operate assigned attribute {attribute} on the grouper group {group}.'''
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/assignAttributesWithValue/WsSampleAssignAttributesWithValueRestLite_json.txt
    logger.info(f'assigning attributes to {group}')
    data = {
        "WsRestAssignAttributesLiteRequest": {
            "attributeAssignOperation":"assign_attr",
            "attributeAssignType":"group",
            "attributeAssignValueOperation":operation,
            "valueSystem":"yes",
            "wsAttributeDefNameName":attribute,
            "wsOwnerGroupName":group
        }
    }
    r = requests.post(f'{base_uri}/attributeAssignments',
        data=json.dumps(data), auth=auth, headers={'Content-type':'text/x-json'}
    )
    out = r.json()
    problem_key = 'WsRestResultProblem'
    if problem_key in out:
        logger.error(f'{problem_key} in output')
        meta = out[problem_key]['resultMetadata']
        raise Exception(meta)
    results_key = 'WsAssignAttributesLiteResults'
    success_codes = ['SUCCESS']
    if results_key in out:
        code = out[results_key]['resultMetadata']['resultCode']
        if code not in success_codes:
            msg = out[results_key]['resultMetadata']['resultMessage']
            raise Exception(f'{code}: {msg}')
    return out
