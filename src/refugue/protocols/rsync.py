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
                               src,
                               target,
    ):
        """Given the high level specification of intended behavior compile the
        appropriate options for rsync."""


        # info
        # info_options = rsync.InfoOptions(
        #     flags=(),
        # )
        info_options = None

        # the key-value options
        opts = {}

        # includes
        if len(src.wset.includes) > 0:
            includes = sec.wset.includes
        else:
            includes = ()

        # excludes
        if len(src.wset.excludes) > 0:
            excludes = sec.wset.excludes
        else:
            excludes = ()

        # policy options
        sync = sync_spec.sync_pol
        transport = sync_spec.transport_pol

        # collect which flags to use

        # always use these ones
        opt_flags = [
            'archive',
            'verbose',
            'human-readable',
            'itemize-changes',
            'stats',
        ]

        # for rsync the transport policy and syncrhonization policy
        # just correspond to different options

        ## Transport
        if transport.dry:
            opt_flags.append('dry-run')

        if transport.compression == 'rsync':
            opt_flags.append('compress')

        if transport.backup == 'rename':
            opt_flags.append('backup')
            opts['suffix'] = '.refugue-backup'

        # TODO: need to get the backup dir from the config..
        # elif transport.backup == 'refile':
        #     opt_flags.append('backup')
        #     opts['backup-dir'] = ''


        ## Sync

        # default to always having the 'update' option on and turned
        # off if we are clobbering

        if not sync.clobber:
            opt_flags.append('update')

        if sync.inject:
            opt_flags.append('existing')

        if sync.clean:
            opt_flags.append('delete')

        if sync.prune:
            opt_flags.append('delete-excluded')


        options = rsync.Options(
            flags=tuple(opt_flags),
            kv=opts,
            includes=includes,
            excludes=excludes,
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
        options = cls._compile_rsync_options(sync_spec, src, target)

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
            target_endpoint = rsync.Endpoint.construct(
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

        # return this closure which is the callable that actually
        # executes the sync process
        def _sync_func(src_cx):
            src_cx.run(command_str)

        return _sync_func, command_str
