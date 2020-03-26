from invoke import task, Collection

from ..config import (
    DEFAULT_USER_SPEC,
    MOCK_HOME,
    SKEL_DIR,
)

import os.path as osp
import os
from pathlib import Path
from crypt import crypt, METHOD_SHA512

import toml

def usernames(users_spec):

    return [users_spec['username_prefix'] + user['id']
            for user in users_spec['users']]

@task
def ls_spec_users(cx, spec=DEFAULT_USER_SPEC):
    """List users managed by this taskset."""

    specced_users = usernames(toml.load(spec))
    print('\n'.join(specced_users))

@task
def ls_active_users(cx,
                    spec=DEFAULT_USER_SPEC,
                    group=None,
):
    """List users managed by this taskset."""

    specced_users = usernames(toml.load(spec))

    # choose which groups to narrow to
    if group is None:
        pass

    else:
        pass

    users = [user for user in pd.getpwall()
             if user]

    print('\n'.join(specced_users))


@task
def clean_users(cx, spec=DEFAULT_USER_SPEC):
    """Remove all users managed by this taskset"""

    pass

@task
def clean_groups(cx, spec=DEFAULT_USER_SPEC):
    """Remove all users managed by this taskset"""

    spec = toml.load(spec)

    for group in spec['groups']:
        cx.run(f"sudo groupdel {group}")


@task
def groups(cx, spec=DEFAULT_USER_SPEC):
    """Make the groups for the user specs."""

    spec = toml.load(spec)

    for group in spec['groups']:
        cx.run(f"sudo groupadd -f {group}")

    return spec['groups']

@task(pre=[clean_users])
def users(cx, spec=DEFAULT_USER_SPEC):
    """Make a new user for this taskset."""

    # create the necessary groups first if not already done
    groups(cx, spec=spec)

    spec = toml.load(spec)


    # read user data from spec
    users = {}
    for user in spec['users']:

        username = spec['username_prefix'] + user['id']
        users[username] = user

    # make sure the mock home dir exists
    mock_home_path = Path(osp.expandvars(osp.expanduser(MOCK_HOME)))
    os.makedirs(mock_home_path,
                exist_ok=True)

    skel_dir_path = Path(osp.expandvars(osp.expanduser(SKEL_DIR)))


    # create the users
    for username, user_spec in users.items():

        group_spec = ','.join(user_spec['groups'])

        # encrypt the password because it needs to be for this method
        password_crypt = crypt(user_spec['password'], METHOD_SHA512)

        # create user with a home in the mock home dir
        cx.run(f"sudo useradd "
               f"--base-dir {mock_home_path} "
               f"--create-home --skel {skel_dir_path} "
               f"--user-group --groups '{group_spec}' "
               f"--shell {user_spec['shell']} "
               f"--password '{password_crypt}' "
               f"{username}")

@task(pre=[clean_users])
def clean(cx):
    pass


# make the collection manually to configure the sudo commands
admin_coll = Collection('admin')

tasks = [
    ls_users,
    clean_users,
    users,
]

for task in tasks:
    admin_coll.add_task(task)
