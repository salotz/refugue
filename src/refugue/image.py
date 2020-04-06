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

from .network import (
    Network,
    Peer,
)
from .sync import (
    SyncProtocol,
    SyncSpec,
)

__all__ = [
    'WorkingSet',
    'Replica',
    'Image',
]


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

        fq_replica = f"{peer.name}/{refinement}"

        ## INCLUDES

        if fq_replica in config['REPLICA_INCLUDES']:
            includes = config['REPLICA_INCLUDES'][fq_replica]

        else:
            includes = []


        ## EXCLUDES

        if fq_replica in config['REPLICA_EXCLUDES']:
            excludes = config['REPLICA_EXCLUDES'][fq_replica]

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

        # STUB: if we want to support defaults in the future do this
        # here

        # I took it out because it was cluttering the config files and
        # doing the prefixes manually isn't that bad and should work
        # with that for a while instead of overcomplicating it.

        # the peer is always the first term in the replica refinement
        tokens = replica_spec.split('/')

        # if there are no tokens left we have to get the default
        # refinement for this host
        if len(tokens) < 2:
            raise ValueError("Full replica refinement must be given at this time")

        peer_spec = tokens[0]

        refinement_spec = '/'.join(tokens[1:])

        return peer_spec, refinement_spec

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

        # STUB: In the future if you want to support default or
        # implicit replica prefixes for certain refinements do it
        # here.

        # I thook them out because it was overcomplicating the config
        # files and not that useful

        assert fq_replica_spec in config['REPLICA_PREFIXES'], \
            f"The replica ({fq_replica_spec}) doesn't have a replica prefix."

        prefix = config['REPLICA_PREFIXES'][fq_replica_spec]

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

@dc.dataclass
class Image():
    """Represents an image distributed across a set of replicas"""

    network : Network
    replicas: Tuple[Replica]

    # TODO: make this more precise
    image_config: Any

    @classmethod
    def from_config(cls, image_config, network):
        """Generate an Image object from a configuration file.

        Parameters
        ----------

        image_config : dict

        network : Network

        Returns
        -------

        image : Image obj

        """

        replicas = Replica.from_config(image_config, network.peers)

        image = Image(
            network = network,
            replicas = replicas,
            image_config = image_config,
        )

        return image

    @staticmethod
    def parse_fq_replica(fq_replica):
        """Parse a string name for a replica into the peer and refinement
        parts as strings."""

        tokens = fq_replica.split('/')
        peer = tokens[0]
        refinement = '/'.join(tokens[1:])

        return peer, refinement


    def get_replica(self, replica_spec):
        """Get a replica by a string name."""

        # normalize and parse
        peer_spec, refinement_spec = Replica.normalize_replica(self.image_config, replica_spec)

        for replica in self.replicas:

            if (peer_spec == replica.peer.name and
                refinement_spec == replica.refinement):

                return replica

    def resolve_replica_path(self,
                             local_cx,
                             replica,
    ):

        replica_cx = self.network.resolve_peer_context(local_cx, replica.peer)
        peer_mount_prefix = self.network.resolve_peer_mount(replica_cx, replica.peer)


        # combine the mount prefix with the replica's path prefix

        # if there is no peer mount prefix leave it out of the template
        if peer_mount_prefix is None:

            replica_path = f"{replica.prefix}"

        else:
            replica_path = f"{peer_mount_prefix}/{replica.prefix}"


        # fully expand the replica prefix if it has variables and such
        # by using the replica's context
        replica_path = replica_cx.run(f'echo "{replica_path}"', hide='out', pty=True).stdout.strip()

        return replica_path

    def pair(self,
             local_cx,
             sync_spec,
             subtree,
             src,
             target,
    ):
        """Make a sync pair from two replicas and a sync spec."""

        src_replica = self.get_replica(src)
        target_replica = self.get_replica(target)

        sync_pair = SyncPair(
            image = self,
            src = src_replica,
            target = target_replica,
            sync_spec = sync_spec,
            subtree = subtree,
        )

        return sync_pair


@dc.dataclass
class SyncPair():

    image: Image
    src: Replica
    target: Replica
    subtree: Optional[Path]
    sync_spec: SyncSpec

    def sync(self,
             local_cx: Context,
             sync_protocol: SyncProtocol,
    ):
        """Perform the sync specified by this SyncPair choosing a protocol to
        do it over, e.g. rsync"""

        # TODO: consider the subpath

        # generate the function
        sync_func, confirm_message = sync_protocol.gen_sync_func(
            local_cx,
            self.image,
            self.src,
            self.target,
            self.sync_spec,
            subtree = self.subtree,
        )
        # return them
        return sync_func, confirm_message
