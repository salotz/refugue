IMAGE_NAME = "tree"

REPLICAS = [
    'ostrich/tree',
    'ostrich/scratch',
    'ostrich/dummy',

    'junco/tree',
    'boxwood/tree',
]

REPLICA_PREFIXES = {

    'ostrich/tree' : '$HOME/tree',
    'ostrich/scratch' : '$HOME/scratch/tree',
    'ostrich/dummy' : '$HOME/scratch/dummy_refugue',

    'junco/tree' : '$HOME/tree',

    # drives
    'boxwood/tree' : '$USER/tree',

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

    'ostrich/dummy' : (
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
    'ostrich/dummy' : [],

    'junco/tree' : [],

    'boxwood/tree' : [],

}
