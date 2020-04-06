from pathlib import Path
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

from refugue.network import (
    RefugueNetworkError,
    LocalConnection,
    ImpossibleConnection,
    SSHConnection,
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
        if len(target.wset.includes) > 0:
            includes = target.wset.includes
        else:
            includes = ()

        # excludes
        if len(target.wset.excludes) > 0:
            excludes = target.wset.excludes
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
                      subtree = None,
    ) -> Callable[[Context], None]:

        ## Validate

        # validate the sync spec for this protocol
        if not cls.validate_sync_spec(sync_spec):
            raise ValueError(f"Invalid SyncSpec for this protocol: {self.__name__}")

        ## Compile Sync Spec to Options
        options = cls._compile_rsync_options(sync_spec, src, target)

        ## Generate enpoint URLs

        # get the paths the file paths for the replicas
        src_replica_path = Path(image.resolve_replica_path(
            local_cx,
            src,
        ))

        target_replica_path = Path(image.resolve_replica_path(
            local_cx,
            target,
        ))

        if subtree is not None:

            src_replica_path = src_replica_path / subtree
            target_replica_path = target_replica_path / subtree

        # generate the rsync.Endpoints

        # get the conn specs for user and host etc.

        src_conn = image.network.resolve_peer_connection(src.peer)
        target_conn = image.network.resolve_peer_connection(target.peer)

        # one or the other can be remote but not both. We can't always
        # rely on the source being local since endpoints you are
        # running from may not be IP addressable so we want to allow
        # for remote 'pull' as well as 'push'

        # so determine whether each endpoint is remote, local, or
        # unreachable to the invocation context:

        src_reachable = (False
                         if issubclass(type(src_conn), ImpossibleConnection)
                         else True)
        target_reachable = (False
                            if issubclass(type(target_conn), ImpossibleConnection)
                            else True)

        # raise the error if either are unreachable
        if not src_reachable:
            raise RefugueNetworkError(f"Unreachable peer: {src.peer.name}")

        if not target_reachable:
            raise RefugueNetworkError(f"Unreachable peer: {target.peer.name}")


        # determine which locality to execute command on
        src_local = (True
                     if issubclass(type(src_conn), LocalConnection)
                     else False)
        target_local = (True
                        if issubclass(type(target_conn), LocalConnection)
                        else False)

        if src_local and target_local:

            # both local doesn't matter, execute on src
            ex_endpoint = 'src'

            src_endpoint = rsync.Endpoint.construct(
                path=str(src_replica_path),
            )

            target_endpoint = rsync.Endpoint.construct(
                path=str(target_replica_path),
            )

        elif (not src_local and not target_local):

            # neither are local execute on src by convention
            ex_endpoint = 'src'


            # make the src endpoint local
            src_endpoint = rsync.Endpoint.construct(
                path=str(src_replica_path),
            )

            target_endpoint = rsync.Endpoint.construct(
                path=str(target_replica_path),
                user=target_conn['user'],
                host=target_conn['host'],
            )


        elif src_local and not target_local:

            # execute on src
            ex_endpoint = 'src'

            src_endpoint = rsync.Endpoint.construct(
                path=str(src_replica_path),
            )

            target_endpoint = rsync.Endpoint.construct(
                path=str(target_replica_path),
                user=target_conn['user'],
                host=target_conn['host'],
            )

        elif target_local and not src_local:

            # execute on target
            ex_endpoint = 'target'

            src_endpoint = rsync.Endpoint.construct(
                path=str(src_replica_path),
                user=src_conn.user,
                host=src_conn.host,
            )


            target_endpoint = rsync.Endpoint.construct(
                path=str(target_replica_path),
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

        if ex_endpoint == 'src':

            def _sync_func(local_cx, src_cx, target_cx):

                src_cx.run(command_str, pty=True)

        elif ex_endpoint == 'target':

            def _sync_func(local_cx, src_cx, target_cx):

                target_cx.run(command_str, pty=True)



        return _sync_func, command_str
