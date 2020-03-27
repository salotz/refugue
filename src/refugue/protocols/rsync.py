import dataclasses as dc
from typing import (
    Optional,
    Union,
    Tuple,
    Callable,
    Mapping,
    Any,
)

from invoke import Context
import py_rsync as rsync

from refugue.image import (
    Replica,
    Image,
)
from refugue.sync import (
    SyncProtocol,
    SyncSpec,
)

@dc.dataclass
class RsyncProtocol(SyncProtocol):

    @classmethod
    def validate_sync_spec(cls,
                           sync_spec: SyncSpec,
    ):
        """Validate that the sync_spec is supported by this protocol."""

        # TODO
        # raise NotImplementedError

        return True

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
                      local_cx: Context,
                      image: Image,
                      src: Replica,
                      target: Replica,
                      sync_spec: SyncSpec,
    ) -> Callable[[Context], None]:

        ## Validate

        # validate the sync spec for this protocol
        if not cls.validate_sync_spec(sync_spec):
            raise ValueError(f"Invalid SyncSpec for this protocol: {self.__name__}")

        ## Compile Sync Spec to Options

        # STUB, TODO: for now its just None for testing
        options = None

        ## Generate enpoint URLs

        # get the conn specs for user and host etc.
        src_conn = image.network.resolve_peer_connection(src.peer)
        target_conn = image.network.resolve_peer_connection(target.peer)

        # get the paths the file paths for the replicas
        src_replica_path = image.resolve_replica_path(
            local_cx,
            src,
        )

        target_replica_path = image.resolve_replica_path(
            local_cx,
            target,
        )


        # generate the rsync.Endpoints
        if src_conn is None:
            src_endpoint = rsync.Endpoint.construct(
                path=src_replica_path,
            )
        else:
            src_endpoint = rsync.Endpoint.construct(
                path=src_replica_path,
                user=src_conn['user'],
                host=src_conn['host'],
            )

        if target_conn is None:
            target_endpoint = rsync.Endpoint.construct(
                path=target_replica_path,
            )
        else:
            target_endpoint = rsync.Endpoint(
                path=target_replica_path,
                user=target_conn['user'],
                host=target_conn['host'],
            )


        # generate the rsync command
        command = rsync.Command(
            src=src_endpoint,
            dest=target_endpoint,
            options=options,
        )

        ## Generate the execution function

        # render the command
        command_str = command.render()

        print("The generated command: ")
        print(command_str)

        # return this closure which is the callable that actually
        # executes the sync process
        def _sync_func(src_cx):
            src_cx.run(command_str)

        return _sync_func
