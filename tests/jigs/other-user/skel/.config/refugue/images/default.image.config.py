# by convention values which are not read by the configuration parser
# are written in snake_case, those that are in all caps.


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
    'ostrich/dummy' : [],

    'junco/tree' : [],

    'boxwood/tree' : [],

}

