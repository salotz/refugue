import dataclasses as dc
from pathlib import Path
from enum import Enum
from typing import (
    Optional,
    Union,
    Tuple,
    Callable,
)

from fabric import connection
import py_rsync as rsync

__all__ = [
    'WorkingSet',
    'PeerType',
    'Peer',
    'PeerHost',
    'PeerDrive',
    'Connection',
    'Replica',
    'Image',
]


@dc.dataclass
class Connection():
    """Abstract connection."""

    host: str
    user: str
    # TODO: implement jump connection
    # jumps: Optional[ Tuple[Connection] ]

def concrete_connection(conn):

    return _fabric_connection(conn)

def _fabric_connection(conn):

    fconn = Connection(
        conn.host,
        user=conn.user
    )

    return conn


class PeerType(Enum):
    HOST = 1
    DRIVE = 2

@dc.dataclass
class Peer():

    name: str

@dc.dataclass
class PeerHost(Peer):

    aliases: Optional[ Tuple[str] ]
    node_aliases: Optional[ Tuple[str] ]

@dc.dataclass
class PeerDrive(Peer):

    pass

@dc.dataclass
class WorkingSet():

    name: str
    includes: Union[ Tuple[str], Ellipsis ]
    excludes: Union[ Tuple[str], Ellipsis ]

@dc.dataclass
class Replica():

    peer: Peer
    refinement: Tuple[str]
    wset: WorkingSet
    prefix: Path

    # TODO
    def resolve_url(self, cx):

        raise NotImplementedError

        return url

    # TODO
    def get_context(self):
        """Get an invoke context or fabric connection for the replica."""

        raise NotImplementedError

        return self_cx


@dc.dataclass
class Image():

    pass

@dc.dataclass
class Network():

    peers: Tuple[Peer]
    replicas: Tuple[Peer]
    image: Image


## Sync specs

@dc.dataclass
class SyncPolicy():
    """A protocol-agnostic specification of a desired synchronization
    between two replicas. This does not include things like working
    sets but rather behaviors for merging, updating, backups, one-way,
    two-way etc.

    Also doesn't include things like encryption or compression.

    """

    # WIP: this is very WIP and based on my previous stuff with rsync
    # do not consider stable at all
    dry: bool
    safe: bool
    ow_sync: bool
    clean: bool
    force: bool

@dc.dataclass
class TransportPolicy():
    """Policy regarding details about how a transport should take place
    including encryption and compression."""

    compress: bool
    encrypt: bool

@dc.dataclass
class SyncSpec():

    sync_pol: SyncPolicy
    transport_pol: TransportPolicy

# protocols

@dc.dataclass
class SyncProtocol():

    @classmethod
    def validate_sync_spec(cls,
                           sync_spec: SyncSpec,
    ):
        """Validate that the sync_spec is supported by this protocol."""

        NotImplemented

    @classmethod
    def gen_sync_func(cls,
                      cx: Context,
                      src: Replica,
                      target: Replica,
                      sync_spec: SyncSpec,
    ) -> Callable[[Context], None]:

        if not cls.validate_sync_spec(sync_spec):
            raise ValueError(f"Invalid SyncSpec for this protocol: {self.__name__}")

        NotImplemented


@dc.dataclass
class RsyncSyncProtocol(SyncProtocol):

    @classmethod
    def validate_sync_spec(cls,
                           sync_spec: SyncSpec,
    ):
        """Validate that the sync_spec is supported by this protocol."""

        raise NotImplementedError

        pass

    @classmethod
    def _compile_rsync_options(cls,
                               sync_spec: SyncSpec,
    ):
        """Given the high level specification of intended behavior compile the
        appropriate options for rsync."""


        # TODO: read spec

        info_options = rsync.InfoOptions(
            flags=(),
        )

        options = rsync.Options(
            flags=(),
            includes=(),
            excludes=(),
            info=info_options,
        )

        return options



    @classmethod
    def gen_sync_func(cls,
                      cx: Context,
                      src: Replica,
                      target: Replica,
                      sync_spec: SyncSpec,
    ) -> Callable[[Context], None]:

        # validate the sync spec for this protocol
        if not cls.validate_sync_spec(sync_spec):
            raise ValueError(f"Invalid SyncSpec for this protocol: {self.__name__}")

        # convert the replicas to a URL
        src_url = src.resolve_url(cx)
        dest_url = dest.resolve_url(cx)

        # the command will be evaluated from the src replica so get
        # the context to it which is potentially remote via
        # fabric.Connection
        src_cx = src_replica.get_context()

        # generate the rsync command
        command = rsync.Command(
            src=rsync.Endpoint(src_url.path, src_url.user, src_url.host),
            dest=rsync.Endpoint(dest_url.path, dest_url.user, dest_url.host),
            options=options,
        )

        # return this closure which is the callable that actually
        # executes the sync process
        def _sync_func(src_cx):
            cx.run(command.render())

        return _sync_func


@dc.dataclass
class SyncPair():

    src: Replica
    target: Replica

    def sync(self,
             cx: Context,
             sync_protocol: SyncProtocol,
             sync_spec: SyncSpec,
    ):

        # TODO: check to see if this connection is possible given
        # current network topology

        # then just run
        sync_func = sync_protocol.gen_sync_func(
            cx,
            self.src,
            self.target,
            sync_spec,
        )

        sync_func(cx)


## from original

def check_fq_replica(replica_spec):

    tokens = replica_spec.split('/')

    passes = True

    if len(tokens) < 2:
        passes = False

        #raise ValueError("No refinement given for the peer")

    return passes


def normalize_replica(replica):
    """Take a partial replica spec and return the fully-qualified one
    (normalized).

    Replicas which are already normalized will be returned unaltered.

    """

    # the peer is always the first term in the replica refinement
    tokens = replica.split('/')

    peer = tokens.pop(0)

    # if there are no tokens left we have to get the default
    # refinement for this host
    if len(tokens) == 0:

        # if a specific default refinement is set for this peer, then
        # use that
        if peer in DEFAULT_PEER_REFINEMENTS:
            refinement = DEFAULT_PEER_REFINEMENTS[peer]

        # otherwise choose the appropriate default for the peer or peer type
        else:

            peer_type = resolve_peer_type(peer)

            if peer_type is None:
                raise ValueError(
                    "Unknown peer and peer type for replica {} cannot resolve a refinement".format(
                        replica))

            else:
                if peer_type in DEFAULT_PEER_TYPE_REFINEMENTS:
                    refinement = DEFAULT_PEER_TYPE_REFINEMENTS[peer_type]
                else:
                    raise ValueError(
                        "No default refinement set for this peer type {}".format(
                            peer_type))

    # otherwise just put the refinement back together and return
    else:
        refinement = '/'.join(tokens)

    # return the fully-qualified replica name
    fq_replica = '{}/{}'.format(peer, refinement)

    return fq_replica

def resolve_peer_type(peer):

    peer_type = None

    if peer in HOSTS:
        peer_type = 'host'

    elif peer in DRIVES:
        peer_type = 'drive'

    return peer_type

def resolve_peer_mount(peer, local_context):
    """Given a peer identity and the local context determine the context
    that should be used to access it (either a fabric.Connection for
    remote or a invoke.Context for local).

    """

    peer_type = resolve_peer_type(peer)

    # HOST peers can be across a network and found via a Connection
    if peer_type == 'host':

        # check to see if our local context is on the peer, by getting
        # the node of the peer and the node we are on (the node is not
        # a fully-qualified domain name FQDN and is what is returned
        # by `platform.node()`)

        # first resolve the alias of the peer if there is one
        if peer in HOST_NODE_ALIASES:
            peer_node_aliases = HOST_NODE_ALIASES[peer]

        # otherwise the peer name is the node name
        else:
            peer_node_aliases = [peer]

        # if the peer is this node we choose the local_context as the
        # peer context
        if platform.node() in peer_node_aliases:
            context = local_context

        # otherwise we get the connection spec for this peer and
        # generate a Connection object for it
        else:
            context = construct_connection(HOST_CONNECTIONS[peer])

        # STUB: This isn't needed but shows a wayt o move forward in
        # generalization

        # # Since hosts cannot be mounted on other hosts, we assume that
        # # the host peer is the root file-system (i.e. is mounted on
        # # the hardware 'hw')
        # mount_spec = ('host', 'hw')

        # # the directory
        # mount_type_dir = PEER_MOUNT_PREFIX_TYPES[mount_spec]

        # # STUB: Alternatively we can look for hosts which are mounted
        # # to the local host peer node. This assert just says that we
        # # expect this to only be the None spec I.e. no path
        # assert mount_type_dir is None

        mount_prefix = None


    # DRIVE peers are assumed to be mounted on the local host node
    # peer
    elif peer_type == 'drive':

        # the context is always the local one
        context = local_context

        mount_spec = ('drive', 'host')

        # STUB: in the future we may support remote drives mounted on
        # other hosts, which will be handled with a peer mini-DSL
        # e.g. 'drive@host' or something similar

        # STUB: we only support drives at a single place without
        # customization. If you want to customize this make a new
        # grouping and set the option in PEER_MOUNT_PREFIX_TYPES

        # get the directory where drives are mounted in
        mount_type_dir = PEER_MOUNT_PREFIX_TYPES[mount_spec]

        # complete it with the name of the drive peer
        mount_prefix = osp.join(mount_type_dir, peer)

    elif peer_type is None:
        raise ValueError("Unknown peer type {} for peer {}".format(peer_type, peer))
    else:
        raise ValueError("Unknown peer type {} for peer {}".format(peer_type, peer))

    return context, mount_prefix

def parse_fq_replica(fq_replica):

    tokens = fq_replica.split('/')
    peer = tokens[0]
    refinement = '/'.join(tokens[1:])

    return peer, refinement

def resolve_replica(p_replica, local_ctx):
    """Takes either a partially or fully-qualified replica spec."""

    # get the peer and it's refinement
    fq_replica = normalize_replica(p_replica)

    # resolve the replica prefix path for the replica
    replica_prefix = resolve_replica_prefix(fq_replica)

    peer, refinement = parse_fq_replica(fq_replica)

    # resolve the connection and the mount prefix for the peer given
    # our current execution environment
    peer_ctx, peer_mount_prefix = resolve_peer_mount(peer, local_ctx)

    # if there is no peer mount prefix leave it out of the template
    if peer_mount_prefix is None:

        replica_path = "{replica_prefix}/{root}".format(
            replica_prefix=replica_prefix,
            root=ROOT_NAME,
        )

    else:
        replica_path = "{peer_mount_prefix}/{replica_prefix}/{root}".format(
            peer_mount_prefix=peer_mount_prefix,
            replica_prefix=replica_prefix,
            root=ROOT_NAME,
        )

    return fq_replica, peer, peer_ctx, replica_path

def resolve_replica_prefix(fq_replica):
    """Given a FQ replica spec, return the replica prefix path for the
    replica peer."""

    assert check_fq_replica(fq_replica), \
        "Replica spec {} is not fully qualified".format(fq_replica)

    # if the exact replica has been specified this takes precedence
    if fq_replica in REPLICA_PREFIXES:
        prefix = REPLICA_PREFIXES[fq_replica]

    # otherwise we attempt to use the defaults for the refinement
    else:

        peer, refinement = parse_fq_replica(fq_replica)

        if refinement in REFINEMENT_REPLICA_PREFIXES:
            prefix = REFINEMENT_REPLICA_PREFIXES[refinement]

        # if there is none it is an error
        else:
            raise ValueError("No prefix found for the replica: {}".format(fq_replica))

    return prefix

def is_default_refinement(fq_replica):

    assert check_fq_replica(fq_replica), \
        "Replica spec {} is not fully qualified".format(fq_replica)

    peer, refinement = parse_fq_replica(fq_replica)
    peer_type = resolve_peer_type(peer)

    if peer in DEFAULT_PEER_REFINEMENTS:
        def_ref = DEFAULT_PEER_REFINEMENTS[peer]

    elif peer_type in DEFAULT_PEER_TYPE_REFINEMENTS:
        def_ref = DEFAULT_PEER_TYPE_REFINEMENTS[peer_type]

    else:
        def_ref = None

    if refinement == def_ref:
        return True

    elif def_ref is None:
        return False

    else:
        return False


def get_working_sets(fq_replica):
    """Given a fq-replica return the working set (includes and excludes)
    for it."""

    assert check_fq_replica(fq_replica), \
        "Replica spec {} is not fully qualified".format(fq_replica)

    peer, refinement = parse_fq_replica(fq_replica)
    default_refinement_flag = is_default_refinement(fq_replica)

    # if the FQ replica is in the includes this takes precedence
    if fq_replica in REPLICA_INCLUDES:
        includes = REPLICA_INCLUDES[fq_replica]

    # otherwise if this refinement is the default one we look to see
    # if the default partially qualified replica is in the list,
    # e.g. for 'host/home' fq-replica we probably will find just
    # 'host' in the listing
    elif peer in REPLICA_INCLUDES and default_refinement_flag:
        includes = REPLICA_INCLUDES[peer]

    else:
        includes = []

    if fq_replica in REPLICA_EXCLUDES:
        excludes = REPLICA_EXCLUDES[fq_replica]

    # otherwise if this refinement is the default one we look to see
    # if the default partially qualified replica is in the list,
    # e.g. for 'host/home' fq-replica we probably will find just
    # 'host' in the listing
    elif peer in REPLICA_EXCLUDES and default_refinement_flag:
        excludes = REPLICA_EXCLUDES[peer]

    else:
        excludes = []


    # handle special values

    # if we exclude '...' we are excluding everything
    if excludes is Ellipsis:
        excludes = ['*']

    # to include everything (...) we just don't tell it to do anything
    if includes is Ellipsis:
        includes = []

    # TODO: make includes ... and excludes ... a warning

    return includes, excludes


def refugue_rsync(local_ctx,
                  source=None,
                  target=None,
                  dry=False,
                  safe=True,
                  ow_sync=False,
                  clean=False,
                  force=False):

    from fabric import Connection

    src_spec = source
    targ_spec = target
    del source
    del target

    print("safe:", safe)

    assert src_spec is not None, "Must give a source"
    assert targ_spec is not None, "Must give a target"

    src_replica, src_peer, src_ctx, src_path = resolve_replica(
                                                    src_spec, local_ctx)
    targ_replica, targ_peer, targ_ctx, targ_path = resolve_replica(
                                                    targ_spec, local_ctx)

    # get the working set spec (includes and excludes) for the target
    includes, excludes = get_working_sets(targ_replica)

    ## Formatting the call to rsync

    # expand shell variables in the paths before formatting
    src_realpath = src_ctx.run('echo "{}"'.format(src_path), hide='out').stdout.strip()
    targ_realpath = targ_ctx.run('echo "{}"'.format(targ_path), hide='out').stdout.strip()

    # if the endpoints are connections extract the url, otherwise just
    # use the paths for the local Context

    # the source URL is always the real path since the command will be
    # executed on the source peer host always
    src_url = src_realpath

    # as for the target it can be more complicated...

    # get whether the endpoints are local or not
    if issubclass(type(src_ctx), Connection):
        src_local = False
    else:
        src_local = True

    if issubclass(type(targ_ctx), Connection):
        targ_local = False
    else:
        targ_local = True


    # if the source is local then we just use the target as is
    # (i.e. if it is not local get a Connection context to it and
    # generate the remote URL)

    # if they are both local then the relative targ is local
    if src_local and targ_local:
        rel_targ_local = True

    # if the source is local and the target is not it is a network
    # transfer
    elif src_local and not targ_local:
        rel_targ_local = False

    # if the source is not local, then we need to figure out if the
    # target is local to that remote or not
    elif not src_local:

        # if target is local relative to the execution point then it
        # is definitely remote, from the remote source
        if targ_local:
            rel_targ_local = False

        # otherwise we need to figure out if the target is on the same
        # host
        else:

            # just compare the peers, if they are on the same peer
            # then it is relatively local
            if src_peer == targ_peer:
                rel_targ_local = True
            else:
                rel_targ_local = False


    # the target is relatively not local to the source, then we
    # prepend the uri for it
    if not rel_targ_local:

        # if the target was remote relative to execution point, then
        # we already have the remote connection information to use for
        # making the connection
        if not targ_local:
            targ_url = "{user}@{host}:{path}".format(
                user=targ_ctx.user,
                host=targ_ctx.host,
                path=targ_realpath)

        # if it is local to the execution point then we need to get
        # the connection information for the URL
        else:

            targ_peer_type = resolve_peer_type(targ_peer)

            # this is easy if it is a host peer
            if targ_peer_type == 'host':
                host_conn_d = HOST_CONNECTIONS[targ_peer]

            # if it is a drive it can be more complicated
            elif targ_peer_type == 'drive':

                # STUB: support finding drives over the network, this
                # is difficult... for now since drives can only be
                # local (an error is raised when you resolve the peer)
                # so we can rely on that and assume that the drive is
                # local to the execution point, that is the "if True"
                if True:

                    targ_host = platform.node()

                    # if this is an alias for a canonical peer name,
                    # replace it with the canonical name
                    for canon_name, aliases in HOST_NODE_ALIASES.items():
                        if targ_host in aliases:
                            targ_host = canon_name
                            break

                    host_conn_d = HOST_CONNECTIONS[targ_host]

                else:
                    raise NotImplementedError("Finding remote drives not supported")

            else:
                raise ValueError("unkown peer type")

            # take the connection values and make the URL
            targ_url = "{user}@{host}:{path}".format(
                user=host_conn_d['user'],
                host=host_conn_d['host'],
                path=targ_realpath)

    else:
        targ_url = targ_realpath

    # decide on compression. If both are local do no compression
    compress = True
    if targ_local and src_local:
        compress = False

    # run the command multiple times if we asked for deletions etc to
    # get the proper information out

    command_str = gen_rsync_command(src_url, targ_url,
                                    includes=includes, excludes=excludes,
                                    dry=dry,
                                    delete=ow_sync,
                                    delete_excluded=clean,
                                    compress=compress,
                                    safe=safe,
                                    force_update=force,
    )

    print("Command generated:")
    print(command_str)

    ## run the thing

    # if the source is remote execute on it's connection
    if issubclass(type(src_ctx), Connection):

        print("Will execute on the source host via Fabric connection.")
    else:
        print("Executing locally.")

    if confirm("Run this command?", assume_yes=False):

        # STUB: trying to handle getting SSH passwords on a remote
        # host for sending stuff back

        # # if the src is remote, we will need to get the password, so
        # # we get it and reconstruct the connection
        # if not src_local:
        #     password = getpass.getpass("SSH key password on {}: ".format(src_peer))

        #     targ_ctx =

        # make sure the root exists on the targ
        targ_ctx.run("mkdir -p {}".format(targ_path))

        src_ctx.run(command_str)

