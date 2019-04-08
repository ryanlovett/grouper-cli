grouper-cli
=============
Manage Grouper groups.

Requires Grouper API credentials.

```
usage: grouper [-h] [-B BASE_URI] [-C CREDENTIALS] [-v] [-d]
               {list,find,create,add,attribute} ...

Manage Grouper groups.

positional arguments:
  {list,find,create,add,attribute}
    list                List group and folder members
    find                Find a group
    create              Create a group or folder
    add                 Replace group members
    attribute           Add or remove an attribute on a group

optional arguments:
  -h, --help            show this help message and exit
  -B BASE_URI           Grouper base uri
  -C CREDENTIALS        Credentials file
  -v                    Be verbose
  -d                    Debug
```

Examples
--------

```
# set our grouper endpoint
export GROUPER_BASE_URI="https://calgroups.berkeley.edu/gws/servicesRest/json/v2_2_100"

# shortcut to our class' folder
class_fldr="edu:berkeley:org:stat:classes:2193:stat-c8"
# prefix shortcut to our class' groups
class_prefix="${class_fldr}:stat-classes-2193-stat-c8"

# create folder for a non-existent term in the year 20xx
grouper create -f edu:berkeley:org:stat:classes:2193 \
	-n "20xx NOTERM"

# create folder for stat-c8 in 20xx NOTERM
grouper create -f edu:berkeley:org:stat:classes:2193:stat-c8 \
	-n "Stat C8"

# create group in stat-c8 NOTERM 20xx for course constituents
grouper create -g ${class_prefix}-enrolled     -n Enrolled
grouper create -g ${class_prefix}-waitlisted   -n Waitlisted
grouper create -g ${class_prefix}-gsis         -n GSIs
grouper create -g ${class_prefix}-instructors  -n Instructors
grouper create -g ${class_prefix}-non-enrolled -n Non-enrolled
grouper create -g ${class_prefix}-admins       -n Admins
grouper create -g ${class_prefix}-all          -n "Test Stat C8"

# replace group members -- uids
grouper replace -g ${class_prefix}-enrolled 12345 23456
grouper replace -g ${class_prefix}-enrolled `cat enrolled.txt`
grouper replace -g ${class_prefix}-enrolled 12345 23456 -i /path/to/more/uids.txt
cat /path/to/uids.txt | grouper replace -g ${class_prefix}-enrolled -i -

# replace group members -- path ids of other groups
grouper replace -g ${class_prefix}-all \
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
