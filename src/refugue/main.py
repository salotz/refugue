

@task()
def refugue_rsync(local_ctx, source=None, target=None,
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


@task
def refugue_list_backups(local_cx, replica=None):

    assert replica is not None, "Must give replica"

    replica, peer, cx, path = resolve_replica(replica, local_cx)

    print("getting real path")
    realpath = cx.run('echo "{}"'.format(path), hide='out').stdout.strip()
    print(realpath)

    print("Running find.")

    cx.run('find {} -name "*.rsync_backup" -print'.format(realpath))



@task
def refugue_diff_backups(local_cx, replica=None):

    assert replica is not None, "Must give replica"

    replica, peer, cx, path = resolve_replica(replica, local_cx)

    print("getting real path")
    realpath = cx.run('echo "{}"'.format(path), hide='out').stdout.strip()
    print(realpath)

    print("Running find.")

    result = cx.run('find {} -name "*.rsync_backup" -print'.format(realpath), hide=True)
    backup_paths = [Path(p) for p in result.stdout.strip().split('\n')]

    # for each backup find the corresponding file
    diff_pairs = []
    for backup_path in backup_paths:
        path = backup_path.parent / backup_path.stem

        print("--------------------------------------------------------------------------------")
        print("DIFF FOR: {}".format(path))
        cx.run("diff {} {}".format(path, backup_path))


@task
def refugue_remove_backups(local_cx, replica=None):

    from fabric import Connection

    assert replica is not None, "Must give replica"

    replica, peer, cx, path = resolve_replica(replica, local_cx)

    print("getting real path")
    realpath = cx.run('echo "{}"'.format(path), hide='out').stdout.strip()
    print(realpath)

    # if the source is remote execute on it's connection
    if issubclass(type(cx), Connection):

        print("Will execute on the source host via Fabric connection.")
    else:
        print("Executing locally.")

    command = 'find {} -name "*.rsync_backup" -delete'.format(realpath)
    print(command)
    if confirm("Run this?", assume_yes=False):
        print("Running find....")
        cx.run(command)
