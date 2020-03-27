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
class Network():

    peers: Tuple[Peer]
    # TODO: make this more exact
    network_config: Any

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

        network = Network(
            peers=peers,
            network_config=config,
        )

        return network



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
            if peer.name in self.network_config['HOST_NODE_ALIASES']:
                peer_node_aliases = self.network_config['HOST_NODE_ALIASES'][peer.name]

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
                peer_cx = self.construct_connection(
                    self.network_config['CONNECTIONS'][peer.name])

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

            # Since hosts cannot be mounted on other hosts, we assume that
            # the host peer is the root file-system (i.e. is mounted on
            # the hardware 'hw')
            mount_spec = ('host', 'hw')

            # the directory, ie.
            # mount_prefix = None

            mount_prefix = self.network_config['PEER_MOUNT_PREFIX_TYPES'][mount_spec]

            # # IDEA: Alternatively we can look for hosts which are mounted
            # # to the local host peer node. This assert just says that we
            # # expect this to only be the None spec I.e. no path
            # assert mount_type_dir is None


        elif peer.peer_type == PeerTypes.drive:

            mount_spec = ('drive', 'host')

            # IDEA: in the future we may support remote drives mounted on
            # other hosts, which will be handled with a peer mini-DSL
            # e.g. 'drive@host' or something similar

            # IDEA: we only support drives at a single place without
            # customization. If you want to customize this make a new
            # grouping and set the option in PEER_MOUNT_PREFIX_TYPES

            # get the directory where drives are mounted in
            mount_type_dir = Path(self.network_config['PEER_MOUNT_PREFIX_TYPES'][mount_spec])

            # complete it with the name of the drive peer
            mount_prefix = mount_type_dir / peer.name


        return mount_prefix

