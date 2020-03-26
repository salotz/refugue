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
import pwd
import grp

import toml

def usernames(users_spec):

    return [users_spec['username_prefix'] + user['id']
            for user in users_spec['users']]

@task
def ls_spec_users(cx, spec=DEFAULT_USER_SPEC):
    """List users managed by this taskset."""

    specced_users = usernames(toml.load(spec))
    print('\n'.join(specced_users))

    return specced_users

@task
def ls_active_users(cx,
                    spec=DEFAULT_USER_SPEC,
):
    """List users managed by this taskset."""

    users_spec = toml.load(spec)

    specced_users = usernames(users_spec)

    active_users = [user.pw_name for user in pwd.getpwall()
                    if user.pw_name in specced_users]

    print('\n'.join(active_users))

    return active_users


@task
def clean_users(cx, spec=DEFAULT_USER_SPEC):
    """Remove all users managed by this taskset"""

    active_users = ls_active_users(cx, spec=spec)

    for user in active_users:
        cx.sudo(f"deluser --remove-home {user}")

    return active_users

@task
def clean_groups(cx, spec=DEFAULT_USER_SPEC):
    """Remove all users managed by this taskset"""

    spec = toml.load(spec)

    for group in spec['groups']:
        cx.sudo(f"groupdel {group}")

    return spec['groups']


@task
def groups(cx, spec=DEFAULT_USER_SPEC):
    """Make the groups for the user specs."""

    spec = toml.load(spec)

    for group in spec['groups']:
        cx.sudo(f"groupadd -f {group}")

    return spec['groups']

@task(pre=[groups])
def add_curr_user_groups(cx, spec=DEFAULT_USER_SPEC):
    """Add the current user to all of the groups in the spec."""

    spec = toml.load(spec)

    username = cx.run("echo $USER").stdout.strip()

    print(f"Adding {username} to the groups: {', '.join(spec['groups'])}")

    for group in spec['groups']:
        cx.sudo(f"usermod -aG {group} $USER")

@task(pre=[])
def rm_curr_user_groups(cx, spec=DEFAULT_USER_SPEC):
    """Add the current user to all of the groups in the spec."""

    spec = toml.load(spec)

    # make the groups spec string, by removing the groups in the spec
    groups = cx.run("id -nG $USER").stdout.strip().split(" ")
    for group in spec['groups']:
        groups.remove(group)

    groups = ' '.join(groups)

    print(f"New group spec for user: {groups}")
    cx.sudo(f"usermod -G {groups} $USER")

    print(f"removed from groups: {spec['groups']}")
    return spec['groups']

@task
def chown_repo(cx, spec=DEFAULT_USER_SPEC):
    """Give dev group access to repo"""

    spec = toml.load(spec)

    cx.sudo(f"chown :{spec['dev_group']} -R .")

@task
def unchown_repo(cx, spec=DEFAULT_USER_SPEC):
    """Give group ownership back to the current user."""

    spec = toml.load(spec)

    cx.sudo(f"chown :$USER -R .")

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
        cx.sudo(f"useradd "
               f"--base-dir {mock_home_path} "
               f"--create-home --skel {skel_dir_path} "
               f"--user-group --groups '{group_spec}' "
               f"--shell {user_spec['shell']} "
               f"--password '{password_crypt}' "
               f"{username}")

@task(pre=[clean_users, rm_curr_user_groups, unchown_repo, clean_groups])
def clean(cx):
    pass

@task(pre=[
    clean,
    add_curr_user_groups,
    chown_repo,
    users,
])
def setup(cx):
    """Set up the default testing apparauts, reverse with 'clean'"""
    pass


# make the collection manually to configure the sudo commands
admin_coll = Collection('admin')

tasks = [
    ls_spec_users,
    ls_active_users,
    clean_users,
    users,
    clean_groups,
    groups,
    add_curr_user_groups,
    rm_curr_user_groups,
    chown_repo,
    unchown_repo,
    setup,
    clean,
]

for task in tasks:
    admin_coll.add_task(task)
