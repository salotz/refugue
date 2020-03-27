import dataclasses as dc
from pathlib import Path
from enum import Enum
import platform
from typing import (
    Optional,
    Union,
    Tuple,
    Callable,
    Mapping,
    Any,
)

from invoke import Context
import fabric as fab
import py_rsync as rsync

__all__ = [
    'WorkingSet',
    'PeerTypes',
    'Peer',
    'PeerHost',
    'PeerDrive',
    'Connection',
    'Replica',
    'Image',
]


class PeerTypes(Enum):
    host = 1
    drive = 2

@dc.dataclass
class Peer():

    name: str
    aliases: Optional[ Tuple[str] ]

    # TODO
    # def __repr__(self):
    #     pass

    @classmethod
    def resolve_peer_type(cls, config, peer_spec):

        peer_type = None

        if peer_spec in config['HOSTS']:
            peer_type = 'host'

        elif peer_spec in config['DRIVES']:
            peer_type = 'drive'

        return peer_type


    @classmethod
    def from_config(cls, config):
        """Generate peers from a configuration file.

        Parameters
        ----------

        config : dict

        Returns
        -------

        peers : list of Peer objects

        """

        peers = []
        for peer_name in config['PEERS']:

            if peer_name in config['PEER_ALIASES']:
                aliases = config['PEER_ALIASES'][peer_name]
            else:
                aliases = ()

            if peer_name in config['DRIVES']:

                peer = PeerDrive(
                    name = peer_name,
                    aliases = aliases,
                )

            elif peer_name in config['HOSTS']:

                if peer_name in config['HOST_NODE_ALIASES']:
                    node_aliases = config['HOST_NODE_ALIASES'][peer_name]
                else:
                    node_aliases = ()

                peer = PeerHost(
                    name = peer_name,
                    aliases = aliases,
                    node_aliases = node_aliases,
                )

            else:
                raise ValueError(f"Peer of unkown type: {peer_name}")

            peers.append(peer)

        return peers

@dc.dataclass
class PeerHost(Peer):

    node_aliases: Optional[ Tuple[str] ]
    """Aliases dynamically determined from a node name"""

    peer_type = PeerTypes.host

@dc.dataclass
class PeerDrive(Peer):

    peer_type = PeerTypes.drive

@dc.dataclass
class WorkingSet():

    includes: Union[ Tuple[str], type(Ellipsis) ]
    excludes: Union[ Tuple[str], type(Ellipsis) ]

    # TODO
    # def __repr__(self):
    #     pass

    @classmethod
    def from_config(cls, config, peer, refinement):
        """Generate the working set for the replica spec given the configuration.

        Parameters
        ----------

        config : dict

        peer : Peer obj

        refinement : str

        Returns
        -------

        wset : WorkingSet

        """

        # check if the replica given is the default one
        default_refinement_flag = Replica.is_default_refinement(
            config,
            peer,
            refinement,
        )

        fq_replica = f"{peer}/{refinement}"

        ## INCLUDES

        if fq_replica in config['REPLICA_INCLUDES']:
            includes = config['REPLICA_INCLUDES'][fq_replica]

        # otherwise if this refinement is the default one we look to see
        # if the default partially qualified replica is in the list,
        # e.g. for 'host/home' fq-replica we probably will find just
        # 'host' in the listing
        elif peer.name in config['REPLICA_INCLUDES'] and default_refinement_flag:
            includes = config['REPLICA_INCLUDES'][peer.name]

        else:
            includes = []


        ## EXCLUDES

        if fq_replica in config['REPLICA_EXCLUDES']:
            excludes = config['REPLICA_EXCLUDES'][fq_replica]

        # otherwise if this refinement is the default one we look to see
        # if the default partially qualified replica is in the list,
        # e.g. for 'host/home' fq-replica we probably will find just
        # 'host' in the listing
        elif peer.name in config['REPLICA_EXCLUDES'] and default_refinement_flag:
            excludes = config['REPLICA_EXCLUDES'][peer.name]

        else:
            excludes = []

        ## handle special values

        # if we exclude '...' we are excluding everything
        if excludes is Ellipsis:
            excludes = ['*']

        # to include everything (...) we just don't tell it to do anything
        if includes is Ellipsis:
            includes = []



        wset = WorkingSet(
            includes = includes,
            excludes = excludes,
        )
        return wset

@dc.dataclass
class Replica():

    peer: Peer
    refinement: str
    wset: WorkingSet
    prefix: Path

    # TODO
    # def __repr__(self):
    #     pass

    @classmethod
    def normalize_replica(cls, config, replica_spec):
        """Take a partial replica spec and return the fully-qualified one
        (normalized).

        Replicas which are already normalized will be returned unaltered.

        Parameters
        ----------

        config : dict

        replica_spec : str

        Returns
        -------

        peer_spec : str

        refinement_spec: str

        """

        # the peer is always the first term in the replica refinement
        tokens = replica_spec.split('/')

        peer_spec = tokens.pop(0)

        # if there are no tokens left we have to get the default
        # refinement for this host
        if len(tokens) == 0:

            # if a specific default refinement is set for this peer, then
            # use that
            if peer_spec in config['DEFAULT_PEER_REFINEMENTS']:
                refinement_spec = config['DEFAULT_PEER_REFINEMENTS'][peer_spec]

            # otherwise choose the appropriate default for the peer or peer type
            else:

                # do this via the config
                peer_type = Peer.resolve_peer_type(config, peer_spec)

                if peer_type is None:
                    raise ValueError(
                "Unknown peer and peer type for replica {} cannot resolve a refinement".format(
                            replica_spec))

                else:
                    if peer_type in config['DEFAULT_PEER_TYPE_REFINEMENTS']:
                        refinement_spec = config['DEFAULT_PEER_TYPE_REFINEMENTS'][peer_type]
                    else:
                        raise ValueError(
                            "No default refinement set for this peer type {}".format(
                                peer_type))

        # otherwise just put the refinement back together and return
        else:
            refinement_spec = '/'.join(tokens)

        return peer_spec, refinement_spec

    @classmethod
    def is_default_refinement(cls, config, peer, refinement):

        if peer.name in config['DEFAULT_PEER_REFINEMENTS']:
            def_ref = config['DEFAULT_PEER_REFINEMENTS'][peer]

        elif peer.peer_type in config['DEFAULT_PEER_TYPE_REFINEMENTS']:
            def_ref = config['DEFAULT_PEER_TYPE_REFINEMENTS'][peer.peer_type]

        else:
            def_ref = None

        if refinement == def_ref:
            return True

        elif def_ref is None:
            return False

        else:
            return False


    @classmethod
    def resolve_replica_prefix(cls, config, peer, refinement):
        """Given a FQ replica spec, return the replica prefix path for the
        replica peer.

        Parameters
        ----------

        config : dict

        peer : Peer obj

        refinement : str

        Returns
        -------

        prefix : Path

        """

        assert refinement is not None, "Refinement must be given, i.e. fully-qualified"

        fq_replica_spec = f"{peer.name}/{refinement}"

        # if the exact replica has been specified this takes precedence
        if fq_replica_spec in config['REPLICA_PREFIXES']:

            prefix = config['REPLICA_PREFIXES'][fq_replica_spec]

        # otherwise we attempt to use the defaults for the refinement
        else:

            if refinement in config['REFINEMENT_REPLICA_PREFIXES']:
                prefix = config['REFINEMENT_REPLICA_PREFIXES'][refinement]

            # if there is none it is an error
            else:
                raise ValueError("No prefix found for the replica: {}".format(fq_replica_spec))

        return prefix


    @classmethod
    def from_config(cls, config, peers):
        """Generate replicas from a configuration file.

        Parameters
        ----------

        config : dict

        peers : list of Peer obj.

        Returns
        -------

        replicas : list of replica objects

        """

        replicas = []
        for replica_spec in config['REPLICAS']:

            # figure out the peer for this replica

            replica_peer_spec, refinement = cls.normalize_replica(config, replica_spec)

            peer = [peer for peer in peers
                    if peer.name == replica_peer_spec][0]

            # get the path prefix for this replica on the peer
            prefix_path = cls.resolve_replica_prefix(config, peer, refinement)


            # create a WorkingSet for the replica
            working_set = WorkingSet.from_config(
                config,
                peer,
                refinement,
            )

            replica = Replica(
                peer = peer,
                refinement = refinement,
                prefix = prefix_path,
                wset = working_set,
            )

            replicas.append(replica)

        return replicas

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
    """"""

    @classmethod
    def from_config(cls, config):
        """Generate an Image object from a configuration file.

        Parameters
        ----------

        config : dict

        Returns
        -------

        image : Image obj

        """

        image = Image()

        return image

@dc.dataclass
class Network():

    peers: Tuple[Peer]
    replicas: Tuple[Replica]
    image: Image
    # TODO: either just use the config directly or better get the
    # values from the config need for resolving peers
    config: Any

    # TODO
    # def __repr__(self):
    #     pass

    @classmethod
    def from_config(cls, config):
        """Generate a Network object from a configuration file.

        Parameters
        ----------

        config : dict

        Returns
        -------

        network : Network obj

        """

        peers = Peer.from_config(config)

        replicas = Replica.from_config(config, peers)

        # TODO: Image just a stub for now
        image = Image.from_config(config)

        network = Network(
            peers=peers,
            replicas=replicas,
            image=image,
            config=config,
        )

        return network

    @staticmethod
    def parse_fq_replica(fq_replica):

        tokens = fq_replica.split('/')
        peer = tokens[0]
        refinement = '/'.join(tokens[1:])

        return peer, refinement


    def get_replica(self, replica_spec):

        # normalize and parse
        peer_spec, refinement_spec = Replica.normalize_replica(self.config, replica_spec)

        for replica in self.replicas:

            if (peer_spec == replica.peer.name and
                refinement_spec == replica.refinement):

                return replica


    def construct_connection(self,
                             conn_d,
    ):
        """Construct an object inheriting from invoke.Context for remote
        execution.

        Currently this is achieved through the fabric.Connection class.

        Parameters
        ----------

        conn_d : dict

        Returns
        -------

        conn : Context subclass

        """

        conn = fab.Connection(
            conn_d['host'],
            user=conn_d['user'],
        )
        return conn

    def resolve_peer_context(self,
                             local_cx,
                             peer,
    ):

        # HOST peers can be across a network and found via a Connection
        if peer.peer_type == PeerTypes.host:

            # check to see if our local context is on the peer, by getting
            # the node of the peer and the node we are on (the node is not
            # a fully-qualified domain name FQDN and is what is returned
            # by `platform.node()`)

            # first resolve the alias of the peer if there is one
            if peer.name in self.config['HOST_NODE_ALIASES']:
                peer_node_aliases = self.config['HOST_NODE_ALIASES'][peer.name]

            # otherwise the peer name is the node name
            else:
                peer_node_aliases = [peer.name]

            # if the peer is this node we choose the local_context as the
            # peer context
            if platform.node() in peer_node_aliases:
                peer_cx = local_cx

            # otherwise we get the connection spec for this peer and
            # generate a Connection object for it
            else:

                # TODO: special error messages for connections that can't be made
                peer_cx = construct_connection(self.config['CONNECTIONS'][peer.name])

        # DRIVE peers are assumed to be mounted on the local host node
        # peer
        elif peer.peer_type == PeerTypes.drive:

            # the context is always the local one
            peer_cx = local_cx


        elif peer.peer_type is None:
            raise ValueError(f"Unknown peer type {peer.peer_type} for peer {peer}")
        else:
            raise ValueError(f"Unknown peer type {peer.peer_type} for peer {peer}")

        return peer_cx

    def resolve_peer_mount(self,
                           peer_cx,
                           peer,
    ):

        if peer.peer_type == PeerTypes.host:

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


        elif peer.peer_type == PeerTypes.drive:

            mount_spec = ('drive', 'host')

            # STUB: in the future we may support remote drives mounted on
            # other hosts, which will be handled with a peer mini-DSL
            # e.g. 'drive@host' or something similar

            # STUB: we only support drives at a single place without
            # customization. If you want to customize this make a new
            # grouping and set the option in PEER_MOUNT_PREFIX_TYPES

            # get the directory where drives are mounted in
            mount_type_dir = Path(self.config['PEER_MOUNT_PREFIX_TYPES'][mount_spec])

            # complete it with the name of the drive peer
            mount_prefix = mount_type_dir / peer.name


        return mount_prefix

    def resolve_replica(self,
                        local_cx,
                        replica,
    ):

        replica_cx = self.resolve_peer_context(local_cx, replica.peer)
        peer_mount_prefix = self.resolve_peer_mount(replica_cx, replica.peer)


        # combine the mount prefix with the replica's path prefix

        # if there is no peer mount prefix leave it out of the template
        if peer_mount_prefix is None:

            replica_path = f"{replica.prefix}"

        else:
            replica_path = f"{peer_mount_prefix}/{replica.prefix}"


        # fully expand the replica prefix if it has variables and such
        # by using the replica's context
        replica_path = replica_cx.run(f'echo "{replica_path}"', hide='out').stdout.strip()

        return replica_cx, replica_path


    def pair(self,
             local_cx,
             src,
             target,
    ):

        src_replica = self.get_replica(src)
        target_replica = self.get_replica(target)

        # get contexts (either Context or fabric Connection objects)
        # for each replica
        src_ctx, src_replica_path = self.resolve_replica(local_cx, src_replica)
        target_ctx, target_replica_path = self.resolve_replica(local_cx, target_replica)

        import pdb; pdb.set_trace()


        sync_pair = SyncPair(
            src = src_replica,
            target = target_replica
        )
        return sync_pair

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
class RsyncProtocol(SyncProtocol):

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
            src_cx.run(command.render())

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

        # generate the function
        sync_func = sync_protocol.gen_sync_func(
            cx,
            self.src,
            self.target,
            sync_spec,
        )

        # and run
        sync_func(cx)
