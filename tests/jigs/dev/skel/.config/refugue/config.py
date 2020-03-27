### Configuration

ROOT_NAME = 'tree'

DRIVES = [
    'boxwood',
]

HOSTS = [
    'ostrich',
    'junco'
]

HOST_NODE_ALIASES = {}

PEER_ALIASES = {}

PEER_TYPES = {
    'hosts' : HOSTS,
    'drives' : DRIVES,
}

PEERS = DRIVES + HOSTS + list(PEER_ALIASES.keys())

PEER_MOUNT_PREFIX_TYPES = {
    ('drive', 'host') : '/media/$USER',
    ('host', 'host') : '/home/$USER/hosts',
    ('host', 'hw') : None,
}

PEER_MOUNTS = {
    # ('honeysuckle', 'superior') : '$HOME/scratch/mount_drives',
}

MISC_CONNECTIONS = {}

HOST_CONNECTIONS = {

    'junco' : {
        'host' : 'junco.salotz.info',
        'user' : 'salotz',
    },

}

CONNECTIONS = {**HOST_CONNECTIONS, **MISC_CONNECTIONS}

DEFAULT_PEER_TYPE_REFINEMENTS = {
    'host' : 'home',
    'drive' : 'user',
}

DEFAULT_PEER_REFINEMENTS = {

}

REPLICAS = PEERS + [
    'ostrich/scratch',
    'ostrich/dummy',
]

REFINEMENT_REPLICA_PREFIXES = {
    # TODO: make this portable somehow so we are querying the target
    # system
    'home' : "$HOME",
    'user' : "$USER",
    'root' : '',
    'scratch' : "$SCRATCH",
}

REPLICA_PREFIXES = {

    'ostrich' : '$HOME/tree',
    'ostrich/scratch' : '$HOME/scratch/tree',
    'ostrich/dummy' : '$HOME/scratch/dummy_refugue',

    'junco' : '$HOME/tree'

    # drives
    'boxwood' : '$USER/tree',

}

BACKUP_EXCLUDES = ['*.stversions', '*.rsync_backup']
VCS_EXCLUDES = ['*.git', '*.hg', '*.svn',]
CACHE_EXCLUDES = ['*__pycache__*']
ENV_EXCLUDES = []
BUILD_EXCLUDES = []

DOMAINS = [
    'dom1',
    'dom2',
]

BASKETS = [
    'incoming',
    'outgoing',
    'resources'
]

ALL_EXCLUDES = DOMAINS + BASKETS

REPLICA_EXCLUDES = {

    'ostrich' : (
        [
            # TODO

        ] +
        (VCS_EXCLUDES +
         CACHE_EXCLUDES +
         BUILD_EXCLUDES +
         BACKUP_EXCLUDES)
    ),

    'ostrich/scratch' : (
        [
            # TODO

        ] +
        (VCS_EXCLUDES +
         CACHE_EXCLUDES +
         BUILD_EXCLUDES +
         BACKUP_EXCLUDES)
    ),

    'ostrich/dummy' : (
        [
            # TODO

        ] +
        (VCS_EXCLUDES +
         CACHE_EXCLUDES +
         BUILD_EXCLUDES +
         BACKUP_EXCLUDES)
    ),

    'junco' : (
        [
            # TODO
        ] +
        (CACHE_EXCLUDES +
         BUILD_EXCLUDES +
         BACKUP_EXCLUDES)
    ),

    # drives
    'boxwood' : (
        [
            # TODO
        ] +
        (BACKUP_EXCLUDES +
         CACHE_EXCLUDES +
         BUILD_EXCLUDES)
    ),
}

REPLICA_INCLUDES = {

    'ostrich' : [],
    'ostrich/scratch' : [],
    'ostrich/dummy' : [],

    'junco' : [],

    'boxwood' : [],

}
