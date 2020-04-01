# By convention the values read by the config reader are in all caps
# and the others are in lower case snake_case

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

backup_excludes = ['*.stversions', '*.rsync_backup']
vcs_excludes = ['*.git', '*.hg', '*.svn',]
cache_excludes = ['*__pycache__*']
env_excludes = []
build_excludes = []

domains = [
    'dom1',
    'dom2',
]

baskets = [
    'incoming',
    'outgoing',
    'resources'
]

all_excludes = domains + baskets

REPLICA_EXCLUDES = {

    'ostrich/tree' : (
        [
            # TODO

        ] +
        (vcs_excludes +
         cache_excludes +
         build_excludes +
         backup_excludes)
    ),

    'ostrich/scratch' : (
        [
            # TODO

        ] +
        (vcs_excludes +
         cache_excludes +
         build_excludes +
         backup_excludes)
    ),

    'junco/tree' : (
        [
            # TODO
        ] +
        (cache_excludes +
         build_excludes +
         backup_excludes)
    ),

    # drives
    'boxwood/tree' : (
        [
            # TODO
        ] +
        (backup_excludes +
         cache_excludes +
         build_excludes)
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
