### Configuration

ROOT_NAME = 'tree'

_DRIVES = []

_HOSTS = []

HOST_NODE_ALIASES = {}

PEER_ALIASES = {}

PEER_TYPES = {
    'hosts' : _HOSTS,
    'drives' : _DRIVES,
}

PEERS = _DRIVES + _HOSTS + list(PEER_ALIASES.keys())

PEER_MOUNT_PREFIX_TYPES = {
    ('drive', 'host') : '/media/$USER',
    ('host', 'host') : '/home/$USER/hosts',
}


PEER_MOUNTS = {}

_MISC_CONNECTIONS = {}

_HOST_CONNECTIONS = {}

CONNECTIONS = {**_HOST_CONNECTIONS, **_MISC_CONNECTIONS}

DEFAULT_PEER_TYPE_REFINEMENTS = {
    'host' : 'home',
    'drive' : 'user',
}

DEFAULT_PEER_REFINEMENTS = {}

REPLICAS = PEERS + []

REFINEMENT_REPLICA_PREFIXES = {
    'home' : "$HOME",
    'user' : "$USER",
}

REPLICA_PREFIXES = {}

_BACKUP_EXCLUDES = ['*~', '*.rsync_backup']
_VCS_EXCLUDES = ['*.git', '*.hg', '*.svn',]
_CACHE_EXCLUDES = ['*__pycache__*']

REPLICA_EXCLUDES = {}

REPLICA_INCLUDES = {}
