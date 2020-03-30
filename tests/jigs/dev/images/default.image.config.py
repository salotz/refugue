IMAGE_NAME = "tree"

REPLICAS = [
    'ostrich/tree',
    'ostrich/scratch',

    'junco/tree',
    'boxwood/tree',
]

REPLICA_PREFIXES = {

    'ostrich/tree' : '$HOME/scratch/refugue/tree',
    'ostrich/scratch' : '$HOME/scratch/refugue/scratch/tree',

    'junco/tree' : '$HOME/scratch/refugue/tree',

    # drives
    'boxwood/tree' : '$USER/scratch/refugue/tree',

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

    'ostrich/tree' : (
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

    'junco/tree' : (
        [
            # TODO
        ] +
        (CACHE_EXCLUDES +
         BUILD_EXCLUDES +
         BACKUP_EXCLUDES)
    ),

    # drives
    'boxwood/tree' : (
        [
            # TODO
        ] +
        (BACKUP_EXCLUDES +
         CACHE_EXCLUDES +
         BUILD_EXCLUDES)
    ),
}

REPLICA_INCLUDES = {

    'ostrich/tree' : [],
    'ostrich/scratch' : [],

    'junco/tree' : [],

    'boxwood/tree' : [],

}


## Pairings

# define the options for syncing between pairs of the replicas

DEFAULT_PAIR_OPTIONS = {
    'sync' : {
         'inject' : False,
         'clobber' : False,
         'clean' : True,
         'prune' : False,
    },

    'transport' : {
        'backup' : 'rename',
        'compression' : 'auto',
        'encryption' : None,
    },
}

PAIR_OPTIONS = {
    ('ostrich/tree', 'boxwood/tree', '<-->') : {
        'sync' : {
            'inject' : False,
            'clobber' : False,
            'clean' : True,
            'prune' : True,
        },

        'transport' : {
            'backup' : 'rename',
            'compression' : 'auto',
            'encryption' : None,
        },
    },
}
