# vim:set et ts=4 sw=4:

import json
import logging

import requests

# logging
logger = logging.getLogger('grouper')

success_codes = [
    'SUCCESS',
    'SUCCESS_INSERTED',
    'SUCCESS_NO_CHANGES_NEEDED',
    'SUCCESS_UPDATED'
]

def boolean_string(b):
    return { True: 'T', False: 'F' }[b]

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

def raise_if_results_error(results_key, out):
    if results_key not in out:
        return
    code = out[results_key]['resultMetadata']['resultCode']
    if code not in success_codes:
        msg = out[results_key]['resultMetadata']['resultMessage']
        raise Exception(f'{code}: {results_key}: {msg}')

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
    raise_if_results_error(results_key, out)
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
    raise_if_results_error(results_key, out)

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
    raise_if_results_error(results_key, out)
    return out

def delete_group(base_uri, auth, group):
    '''Delete a group.'''
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/stemDelete/WsSampleStemDeleteRestLite_json.txt
    logger.info(f'deleting group {group}')

    # the very last stem element
    r = requests.delete(f'{base_uri}/stems/{group}',
        auth=auth
    )
    out = r.json()
    problem_key = 'WsRestResultProblem'
    if problem_key in out:
        logger.error(f'{problem_key} in output')
        meta = out[problem_key]['resultMetadata']
        raise Exception(meta)
    results_key = 'WsStemDeleteLiteResult'
    raise_if_results_error(results_key, out)

def find_group(base_uri, auth, stem, name):
    '''Find a group.'''
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
    raise_if_results_error(results_key, out)
    return out

def add_members(base_uri, auth, group, replace_existing, members):
    '''Replace the members of the grouper group {group} with {users}.'''
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/addMember/WsSampleAddMemberRest_json.txt
    logger.info(f'adding members to {group}')
    data = {
        "WsRestAddMemberRequest": {
            "replaceAllExisting":boolean_string(replace_existing),
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
    raise_if_results_error(results_key, out)
    return out

def delete_members(base_uri, auth, group, members):
    '''Delete {members} of the grouper group {group}.'''
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/addMember/WsSampleAddMemberRest_json.txt
    logger.info(f'deleting members from {group}')
    data = {
        "WsRestDeleteMemberRequest": {
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
        data['WsRestDeleteMemberRequest']['subjectLookups'].append(
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
    results_key = 'WsDeleteMemberResults'
    raise_if_results_error(results_key, out)
    return out

def assign_attribute(base_uri, auth, group, attribute, attr_op, value_op, value=''):
    '''Operate assigned attribute {attribute} on the grouper group {group}.'''
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/assignAttributesWithValue/WsSampleAssignAttributesWithValueRestLite_json.txt
    logger.info(f'assigning attributes to {group}')
    data = {
        "WsRestAssignAttributesLiteRequest": {
            "attributeAssignOperation":attr_op,
            "attributeAssignType":"group",
            "wsAttributeDefNameName":attribute,
            "wsOwnerGroupName":group
        }
    }
    if value_op == 'add_value':
        data["WsRestAssignAttributesLiteRequest"]["valueSystem"] = value
        data["WsRestAssignAttributesLiteRequest"]["attributeAssignValueOperation"] = value_op

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
    raise_if_results_error(results_key, out)
    return out

def group_has_attr(base_uri, auth, group, attribute):
    out = get_assign_attribute(base_uri, auth, attribute, group=group)
    groups = out['WsGetAttributeAssignmentsResults']['wsGroups']
    if len(groups) != 1:
        return False
    retval = groups[0]['name'] == group
    logger.info(f'{group} has {attribute}: {retval}')
    return retval

def get_assign_attribute(base_uri, auth, attribute, group=None, stem=None):
    '''Operate assigned attribute {attribute} on the grouper group {group}.'''
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/getAttributeAssignments/WsSampleGetAttributeAssignmentsRestLite_json.txt
    logger.info(f'getting attribute {attribute} from {group}')
    data = {
        "WsRestGetAttributeAssignmentsLiteRequest": {
            "wsAttributeDefNameName":attribute,
            "attributeAssignType":"group",
            "includeAssignmentsOnAssignments":"F",
        }
    }

    # via https://github.com/rb12345/grouper_ws, which exists and is nicer! :P
    # TODO: use that
    params = {}
    if group is not None:
        params["wsOwnerGroupName"] = group
    elif stem is not None:
        params["wsOwnerStemName"] = stem
    data["WsRestGetAttributeAssignmentsLiteRequest"].update(params)

    r = requests.post(f'{base_uri}/attributeAssignments',
        data=json.dumps(data), auth=auth, headers={'Content-type':'text/x-json'}
    )
    out = r.json()
    problem_key = 'WsRestResultProblem'
    if problem_key in out:
        logger.error(f'{problem_key} in output')
        meta = out[problem_key]['resultMetadata']
        raise Exception(meta)
    results_key = 'WsGetAttributeAssignmentsResults'
    raise_if_results_error(results_key, out)
    return out

def get_subject_memberships(base_uri, auth, subject_id, source_id='ldap'):
    '''Get the groups that a subject (member) belongs to.'''
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/getMemberships/WsSampleGetMembershipsRestLite2_withInput_json.txt
    logger.info(f'getting memberships for subject {subject_id}')
    
    # Build the URL with subject ID
    url = f'{base_uri}/subjects/{subject_id}/memberships'
    
    r = requests.get(url, auth=auth, headers={'Content-type':'text/x-json'})
    out = r.json()
    
    problem_key = 'WsRestResultProblem'
    if problem_key in out:
        logger.error(f'{problem_key} in output')
        meta = out[problem_key]['resultMetadata']
        raise Exception(meta)
    
    results_key = 'WsGetMembershipsResults'
    raise_if_results_error(results_key, out)
    
    # Extract group names from the response
    groups = []
    if results_key in out and 'wsGroups' in out[results_key]:
        for group in out[results_key]['wsGroups']:
            groups.append(group['name'])
    
    logger.info(f'subject {subject_id} is member of {len(groups)} groups')
    return groups

def get_subject_info(base_uri, auth, subject_id, source_id='ldap'):
    '''Get information about a subject including their group memberships.'''
    logger.info(f'getting subject information for {subject_id}')
    
    try:
        # Get the group memberships for this subject
        memberships = get_subject_memberships(base_uri, auth, subject_id, source_id)
        
        return {
            'subject_id': subject_id,
            'source_id': source_id,
            'group_memberships': memberships,
            'membership_count': len(memberships)
        }
    except Exception as e:
        logger.error(f'Error getting subject info for {subject_id}: {e}')
        raise e
