### Configuration

DRIVES = [
    'boxwood',
]

HOSTS = [
    'ostrich',
    'junco'
]

HOST_NODE_ALIASES = {}

PEER_ALIASES = {
    'bigbird' : 'ostrich',
    'refugue-test-drive' : 'boxwood',
    'test-server' : 'junco',
}

PEER_TYPES = {
    'hosts' : HOSTS,
    'drives' : DRIVES,
}

PEERS = DRIVES + HOSTS

PEER_MOUNT_PREFIX_TYPES = {
    ('drive', 'host') : '/media/salotz',
    ('host', 'hw') : None,
}

# TODO: not supported right now, but it should be
PEER_MOUNTS = {
    # put special mount points here
    # ('boxwood', 'ostrich') : '/media/salotz',
}

CONNECTIONS = {

    'junco' : {
        'host' : 'junco.salotz.info',
        'user' : 'salotz',
    },

}
