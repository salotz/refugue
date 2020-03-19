import runpy
import os.path as osp
from pathlib import Path

import click
import fabric

from .main import (
    Replica,
    SyncPair,
    RsyncProtocol,
)

import refugue.config as config


_PROTOCOL_MAPS = (
    ('rsync', RsyncProtocol),
)

@click.command()
@click.option("--config", type=click.Path(exists=True), default="$HOME/.refugue/config.py")
@click.option("--sync-file", type=click.Path(exists=True), default="$HOME/.refugue/sync_specs.toml")
@click.option("--sync", default=None)
@click.option("--transport", default=None)
@click.option("--protocol", default='rsync')
@click.argument("src")
@click.argument("target")
def cli(config, sync_file, sync, protocol, src, target):

    # TODO: calidate options

    # expand shell variables to the config file
    config = Path(osp.expanduser(osp.expandvars(config)))

    # TODO: use runpy to get the declared variables as a dictionary
    config_d = foo()

    # TODO: conjure up a local invoke context to run from
    local_cx = foo()

    # TODO: build the network from the configuration file
    network = Network(**config_d)

    # TODO: do the network discovery to find
    network.discovery(cx)

    src_replica = Replica(src)
    target_replica = Replica(target)

    # identify the replicas in the network, discover current network
    # topology, validate connection viability, and reify
    sync_pair = network.pair(
        src_replica,
        target_replica,
    )


    # choose protocol
    sync_protocol = dict(_PROTOCOL_MAPS)[protocol]

    sync_pair.sync(
        cx,
        sync_protocol,
        
    )

if __name__ == "__main__":

    cli()
