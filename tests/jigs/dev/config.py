### Configuration

ROOT_NAME = 'tree'

## Peers: logical stores (e.g. a filesystem or removable drive)

# peer names must be unique between the different categories of
# peers. The current categories are: drives and hosts

# peers may be mounted onto other peers by either a normal 'mount' for
# drives or some network protocol like sftp. The relationships between
# each category should share the same common directory for mounting
# and are given by the PEER_MOUNTS structure.

DRIVES = [
    'boxwood',
]

HOSTS = [
    'ostrich',
    'junco'
]

# HOSTS can have aliases for the actual name of the node that
# `platform.node()` will return.

HOST_NODE_ALIASES = {}

## Peer Aliases

# STUB: not currently used anywhere. It doesn't really add that much
# except convenience if you don't like or can't remember the actual
# $HOSTNAME of a node. The HOST_NODE_ALIASES on the other hand is
# actually needed because $HOSTNAME or platform.node() will probably
# return something else. These aliases could also allow you to define
# different policies over the aliased value but not for the original
# one.

# aliases for different peers, this allows you to specify different
# connections for different peer names or different mounting strategies
PEER_ALIASES = {}

PEER_TYPES = {
    'hosts' : HOSTS,
    'drives' : DRIVES,
}

PEERS = DRIVES + HOSTS + list(PEER_ALIASES.keys())

## Peer mounts

# the PEER_MOUNT_TYPES specify defaults for different mounting
# scenarios, custom peer mounts can be specified in PEER_MOUNTS

# the directories where peer mount types should be placed. The key is
# (alien, native) where the strings are the identifiers of the
# different peer types (in PEER_TYPES)
PEER_MOUNT_PREFIX_TYPES = {
    ('drive', 'host') : '/media/$USER',
    ('host', 'host') : '/home/$USER/hosts',
    ('host', 'hw') : None,
}


# custom peer mount specifications. This indicates the exact mount
# point for mount pair of peers. This overrides any default in
# PEER_MOUNT_TYPES
PEER_MOUNTS = {
    # Example: if you mount a drive somewhere other than the default above put it here
    # ('honeysuckle', 'superior') : '$HOME/scratch/mount_drives',
}

## Peer Connections

# each peer has a unique connection that can be made to it. This will
# be used to generate a connection object via one of the protocols
# (i.e. rsync or ssh). If a single concrete (i.e. real life) peer has
# multiple ways of connecting to it, make a peer alias (PEER_ALIASES)
# and then make a new connection for that

# connections without matching peers will be treated as bare
# connections that can be referenced by other connections to support
# network jumps, you can also specify this with an extra 'type' :
# 'connection' pair (or to be pedantic 'type' : 'peer' for peers too).

MISC_CONNECTIONS = {}

HOST_CONNECTIONS = {

    'junco' : {
        'host' : 'junco.salotz.info',
        'user' : 'salotz',
    },

}

# general purpose connections for use within fabric automation
CONNECTIONS = {**HOST_CONNECTIONS, **MISC_CONNECTIONS}

### Replicas: specific replicas of the tree

# replicas must start with a peer name and then further be "refined"
# (in the REBOL sense) to the actual replica. This is to support the
# feature that allows multiple replicas to be on a single peer
# (e.g. scratch or backup etc.)

# examples of multiple replicas on the same peer are: 'ostrich/home',
# 'ostrich/scratch'.

# Each peer type has a default refinement. For 'host' and 'drive' type
# peers it is '{peer}/home'

# defaults for broad types of peers. peer types are in PEER_TYPES
DEFAULT_PEER_TYPE_REFINEMENTS = {
    'host' : 'home',
    'drive' : 'user',
}

# default refinements for a specific peer
DEFAULT_PEER_REFINEMENTS = {

}

# but you can add individual refinements by putting them in the block
# below

# TODO: Remove, not sure we even need this
REPLICAS = PEERS + [

    'icer/scratch',

    # testing
    'shrike/dummy',
    'icer/dummy'
]

### Replica Locators

# replicas are replicas of a single tree of files "the tree" (we
# currently do not support different trees, which is best taken care
# of by sub domains or a completely different config file).

# this tree (logical file hierarchy structure not to be confused with
# any concrete implementation of a filesystem) must be "mounted" to an
# existing host file hierarchy at some mount point, which we call the
# replica prefix. The replica prefixes are simply real fully-qualified
# paths on the peer they are to be "hosted" on. These paths must be
# full and start from a root '/'. However, a host itself may be
# mounted to another host in some way (confusing I know). But from the
# point of view of a replica this should be completely transparent and
# not to know anything about this.

# I.e. replica mount points are essentially immutable, while host
# mount points are mobile.

# The mobility of a host mount point simply provides us with a
# protocol for transferring files. A thumb drive called 'bush' mounted
# to a host computer at '/media/$USER/bush' is essentially the same as
# using a protocol prefix for ssh or rsync;
# 'rsync:bush.ether.com'. This of course doesn't make sense for a
# thumb drive since it cannot be located by a computer without being
# plugged into one.

# If the drive was plugged into a computer somewhere over a network
# and we wanted to mount locate it we could do this:
# 'rsync:server.nest.casa/media/$USER/bush'


# To combine a potential network connection we refer to a locator
# which is a combination of a network URL (i.e. protocol:ip/dns) and a
# prefix. The network URL will be implemented as an SSH connection
# through the Fabric Connection object. The prefix will be a simple
# path string called the 'replica prefix' as described above.

# LOCATOR = (CONNECTION, PREFIX)

## Replica Prefixes

REFINEMENT_REPLICA_PREFIXES = {
    # TODO: make this portable somehow so we are querying the target
    # system
    'home' : "$HOME",
    'user' : "$USER",
    'root' : '',
    'scratch' : "$SCRATCH",
}

REPLICA_PREFIXES = {

    # testing
    'ostrich/dummy' : '$HOME/scratch/dummy_refugue',
}

## Replica Connections


# TODO: not need anymore replicas specify the peer which has
# connections built into them. In the future a mini-DSL might be
# useful, but for now it is KV semantics

# # Connections can be specified by name (and only name at this point)
# # prefixing a replica name. The named connection must exist for the
# # replica. If present the connection must come before the replica name
# # and separated by CONNECTION_DELIM

# # specs for the locators that are supported
# CONNECTION_DELIM = "://"


# # By default there exists two connections for each replica: 'local',
# # 'null', and 'sudo'. The 'local' connection is a connetion to
# # 'localhost'. The 'null' connection is not a connection at all and is
# # a specially handled None python value. The 'sudo' connection is an
# # easy way to get superuser access to your local computer without
# # running this stuff as superuser (which has unfamiliar environments
# # etc.). This could be used for managing system config files. TRAMP in
# # emacs uses a similar method for editing files from emacs when emacs
# # was started in a user process.

# LOCAL_CONNECTIONS = {
#     'null' : None,

#     'local' : {
#         'host' : 'localhost',
#         # TODO: localize for the user
#         'user' : '$USER',
#     },

#     'sudo' : {
#         'host' : 'localhost',
#         'user' : 'root',
#     },

# }

# Since host peers already have a set of connections associated with
# them (which can potentially be used for purposes other than
# replicating tree replicas with) we start with those take them to be
# the unrefined replicas named for each.

# TODO: not sure if this is fulfilling any role

# PEER_CONNECTIONS = {

#     # the remote host peer connections
#     **HOST_CONNECTIONS,

#     # STUB: Not supported like this yet
#     # replica specific connections
#     # 'root@superior' : {
#     #     'host' : 'superior.bch.msu.edu',
#     #     'user' : 'root',
#     # },
# }


## Replica Working Sets

# we use includes and excludes (currently exactly as implemented in
# rsync) to specify the working sets each replica gets.

BACKUP_EXCLUDES = ['*.stversions', '*.rsync_backup']
VCS_EXCLUDES = ['*.git', '*.hg', '*.svn',]
CACHE_EXCLUDES = ['*__pycache__*']
ENV_EXCLUDES = []
BUILD_EXCLUDES = []

DOMAINS = [
    'personal',
    'lab',
]

BASKETS = [
    'incoming',
    'outgoing',
    'reading',
    'mobile',
]

UTIL = ['bin',
        'programs',
]

ALL_EXCLUDES = DOMAINS + BASKETS + UTIL

# the lab domain useful exclude aliases
LAB_SEH_JOB_RESULTS = [
    # this will exclude all of the raw results from the simulations,
    # these are unnecessary for data analysis, and once the project is
    # over can be deleted, they only should stick around so that you
    # can reconstruct the trimmed and aggregated HDF5 file.
    'lab/resources/project-resources/seh.pathway_hopping/hpcc/simulations/*/jobs/**wepy.h5'
]

# Ellipsis indicates to NOT include anything, that is exclude everything
REPLICA_EXCLUDES = {

    # testing
    'shrike/dummy' : ['incoming', 'outgoing', 'lab', 'personal'],
    'honeysuckle' : ['outgoing', 'lab', 'personal'],
    'icer/dummy' : ['outgoing', 'lab', 'personal'],

    ##### hosts and filesystems

    ## msu

    # icer
    'icer' : (
        ALL_EXCLUDES +
        [
            'lab/*',
            'lab/projects/*',
            'lab/resources/*',
            'lab/resources/project-resources/*',
        ] +
        LAB_SEH_JOB_RESULTS +
        CACHE_EXCLUDES + BUILD_EXCLUDES + BACKUP_EXCLUDES),

    'icer/scratch' : (
        ALL_EXCLUDES +
        [
            'lab/*',
            'lab/projects/*',
            'lab/resources/*',
            'lab/resources/project-resources/*',
            'lab/resources/project-resources/**.wepy.h5',
        ] +
        LAB_SEH_JOB_RESULTS +
        CACHE_EXCLUDES + BUILD_EXCLUDES + BACKUP_EXCLUDES + VCS_EXCLUDES
    ),

    # biochemistry (bch)
    'superior' : (
        [
            'personal',
            'reading',
            'lab/devel',
            'lab/org',
            'mobile',
        ] +
        LAB_SEH_JOB_RESULTS +
        CACHE_EXCLUDES + BUILD_EXCLUDES + BACKUP_EXCLUDES
    ),

    # salotz net
    'ostrich' : (
        [
            'lab/devel',
            'lab/org',
            'personal/devel',
            'personal/org',
        ] +
        LAB_SEH_JOB_RESULTS +
        VCS_EXCLUDES + CACHE_EXCLUDES + BUILD_EXCLUDES + BACKUP_EXCLUDES
    ),

    'shrike' : (
        [
            'lab/resources/seh.pathway_hopping',
            'lab/resources/project-archives',
            'lab/devel',
            'lab/org',
            'personal/devel',
            'personal/org',
        ] +
        CACHE_EXCLUDES + BUILD_EXCLUDES + BACKUP_EXCLUDES
    ),

    # drives
    'allegheny' : (
        [
            'personal',
            'reading',
            'mobile',
        ] +
        BACKUP_EXCLUDES + CACHE_EXCLUDES
    ),

    'rhododendron' : (
        [
            'lab/',
            'personal/resources/books',
            'personal/resources/music',
            'personal/resources/photos',
            'personal/resources/videos',
            'personal/resources/project-archives',
            'mobile',
        ] +
        CACHE_EXCLUDES + BUILD_EXCLUDES + BACKUP_EXCLUDES + BACKUP_EXCLUDES
    ),

    'birch' : (
        [
            'lab',
        ] +
        CACHE_EXCLUDES + BUILD_EXCLUDES + BACKUP_EXCLUDES + BACKUP_EXCLUDES
    ),

    'dogwood' : Ellipsis,
    'camellia' : Ellipsis,
    'buckthorn' : Ellipsis,

}

REPLICA_INCLUDES = {

    # testing
    'shrike/dummy': [],

    # msu net

    # icer
    'icer' : [
        'lab/',
        'lab/projects/',
        'lab/projects/seh.pathway_hopping/',
        'lab/resources/',
        'lab/resources/project-resources/',
        'lab/resources/project-resources/seh.pathway_hopping/',
    ],

    'icer/scratch' : [
        'lab/',
        'lab/projects/',
        'lab/projects/seh.pathway_hopping/',
        'lab/resources/',
        'lab/resources/project-resources/',
        'lab/resources/project-resources/seh.pathway_hopping/',
    ],

    # bch
    'superior' : [],

    # salotz net
    'ostrich' : [],
    'shrike' : [],

    'allegheny' : [],

    'rhododendron' : [],

    'camellia' : [
        'personal/pim/secrets'
    ],

    'buckthorn' : [
        'personal/pim/secrets/'
    ],

}
