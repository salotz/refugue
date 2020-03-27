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

from .image import (
    Replica,
)

__all__ = [
]


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
