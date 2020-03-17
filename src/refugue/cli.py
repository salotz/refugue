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


_PROTOCOL_MAPS = {
    'rsync' : RsyncProtocol,
}

@click.command()
@click.option("--config", type=click.Path(exists=True), default="$HOME/.refugue/config.py")
@click.option("--protocol", default='rsync')
@click.argument("src")
@click.argument("target")
def cli(config, protocol, src, target):

    # expand shell variables to the config file
    config = Path(osp.expanduser(osp.expandvars(config)))

    # use runpy to get the declared variables as a dictionary

    network = Network

    src_replica = Replica(src)
    target_replica = Replica(target)

    sync_protocol = _PROTOCOL_MAPS[protocol]

    sync_pair = SyncPair(
        src=src_replica,
        target=target_replica,
    )

    sync_pair.sync(sync_protocol)

if __name__ == "__main__":

    cli()
