grouper-cli
=============
Manage Grouper groups.

Requires Grouper API credentials.

```
usage: grouper [-h] [-B BASE_URI] [-C CREDENTIALS] [-v] [-d]
               {list,find,create,add,delete,attribute,subject} ...

Manage Grouper groups.

positional arguments:
  {list,find,create,add,delete,attribute,subject}
    list                List group and folder members
    find                Find a group
    create              Create a group or folder
    add                 Add group members
    delete              Delete group members
    attribute           Add or remove an attribute on a group
    subject             Get information about a subject (member)

optional arguments:
  -h, --help            show this help message and exit
  -B BASE_URI           Grouper base uri
  -C CREDENTIALS        Credentials file
  -v                    Be verbose
  -d                    Debug
```

Examples
--------

Given an academic term and course number:
```
{
    "year": 2019,
    "semester": "summer",
    "class": 14720
}
```
one can create a course folder and group structure.

```
# shortcut to our class' folders
org_fldr="edu:berkeley:org:stat:classes"
term_fldr="${org_fldr}:2019-summer"
class_fldr="${term_fldr}:14720"

# Groups must be unique in some grouper instances. We disambiguate them with
# org, term, and course info in their prefix.
class_prefix="${class_fldr}:stat-classes-2019-summer-14720"

# set our grouper api endpoint
export GROUPER_BASE_URI="https://calgroups.berkeley.edu/gws/servicesRest/json/v2_2_100"

# create folder for the summer 2019 term
grouper create -f ${term_fldr} -n "2019 summer"

# create folder for 14720 (compsci-c8) in 2019 summer
grouper create -f ${class_fldr} -n "Compsci C8"

# create group in stat-c8 NOTERM 20xx for course constituents
grouper create -g ${class_prefix}-enrolled     -n Enrolled
grouper create -g ${class_prefix}-waitlisted   -n Waitlisted
grouper create -g ${class_prefix}-gsis         -n GSIs
grouper create -g ${class_prefix}-instructors  -n Instructors
grouper create -g ${class_prefix}-non-enrolled -n Non-enrolled
grouper create -g ${class_prefix}-admins       -n Admins
grouper create -g ${class_prefix}-all          -n "Test Stat C8"

# add group members -- uids
grouper add -g ${class_prefix}-enrolled 12345 23456
grouper add -g ${class_prefix}-enrolled `cat enrolled.txt`
grouper add -g ${class_prefix}-enrolled 12345 23456 -i /path/to/more/uids.txt
cat /path/to/uids.txt | grouper add -g ${class_prefix}-enrolled -i -

# add group members -- path ids of other groups
grouper add -g ${class_prefix}-all \
	${class_prefix}-enrolled \
	${class_prefix}-waitlisted \
	${class_prefix}-gsis \
	${class_prefix}-instructors \
	${class_prefix}-non-enrolled

# list members
grouper list -g ${class_prefix}-enrolled

# provision group to google
grouper attribute -g ${class_prefix}-all \
	-a etc:attribute:provisioningTargets:googleProvisioner:syncToGooglebcon
# deprovision group to google
grouper attribute -g ${class_prefix}-all \
	-r etc:attribute:provisioningTargets:googleProvisioner:syncToGooglebcon

# get groups that a subject (member) belongs to (default output)
grouper subject -s 1559801

# get full subject information as JSON
grouper subject -s 1559801 --json

# Alternative short form for JSON output
grouper subject -s 1559801 -J

# Example JSON output with --json flag:
# {
#   "subject_id": "1559801",
#   "source_id": "ldap",
#   "group_memberships": [
#     "edu:berkeley:org:stat:classes:2019-summer:14720:enrolled",
#     "edu:berkeley:org:stat:classes:2019-summer:14720:all"
#   ],
#   "membership_count": 2
# }

# get subject info with custom source ID
grouper subject -s 1559801 --source-id ldap

# get JSON output with custom source ID
grouper subject -s 1559801 --source-id ldap --json
```

Credentials
-----------

Supply the Grouper API credentials in a JSON file of the form:
```
{
	"grouper_user": "...",
	"grouper_pass": "..."
}
```
The default file is ./.grouper.json.

Development
-----------

### Running Tests

This project uses pytest for testing. To run the tests:

```bash
# Install test dependencies
pip install -e .[test]

# Run all tests
pytest

# Run tests with coverage
pytest --cov=grouper --cov-report=term-missing

# Run only subject-related tests
pytest tests/test_subject.py

# Run tests with verbose output
pytest -v
```

### Testing the New Subject Functionality

The subject functionality includes comprehensive tests that mock the Grouper API responses. The tests verify:

- Successful retrieval of subject group memberships
- Handling of empty membership responses
- Error handling for invalid subjects
- Parameter validation
- Integration between `get_subject_memberships()` and `get_subject_info()`

Example test run:
```bash
pytest tests/test_subject.py -v
```
