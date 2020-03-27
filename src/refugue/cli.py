import runpy
import os.path as osp
from pathlib import Path
import runpy

from invoke import Context
import click
import fabric

from .main import (
    Network,
    Replica,
    SyncPair,
)

import refugue.config as config


# _PROTOCOL_MAPS = (
#     ('rsync', RsyncProtocol),
# )


DEFAULT_CONFIG_PATH = "$HOME/.config/refugue/config.py"

CONFIG_KEYS = (
    "HOSTS",
    "DRIVES",
    "PEER_ALIASES",
    "HOST_NODE_ALIASES",
    "PEER_TYPES",
    "PEERS",
    "PEER_MOUNT_PREFIX_TYPES",
    "PEER_MOUNTS",
    "CONNECTIONS",
    "DEFAULT_PEER_TYPE_REFINEMENTS",
    "DEFAULT_PEER_REFINEMENTS",
    "REPLICAS",
    "REFINEMENT_REPLICA_PREFIXES",
    "REPLICA_PREFIXES",
    "REPLICA_EXCLUDES",
    "REPLICA_INCLUDES",
)

def read_config(config_path):
    """Read a python code config file and strip out only the recognized
    variables"""

    config_all = runpy.run_path(str(config_path))

    config = {key : value for key, value in config_all.items()
              if key in CONFIG_KEYS}

    return config

@click.command()
@click.option("--config", type=click.Path(exists=True), default=None)
@click.option("--sync-file", type=click.Path(exists=True), default=None)
@click.option("--sync", default=None)
@click.option("--transport", default=None)
@click.option("--protocol", default=None)
@click.argument("src")
@click.argument("target")
def cli(config, sync_file, sync, transport, protocol, src, target):

    if config is None:
        config = DEFAULT_CONFIG_PATH

    # TODO: validate options

    # expand shell variables to the config file
    config_path = Path(osp.expanduser(osp.expandvars(config)))

    config_d = read_config(config_path)

    # conjure up a local invoke context to run from
    local_cx = Context()

    # build the network from the configuration file
    network = Network.from_config(config_d)

    # identify the replicas in the network, discover current network
    # topology, validate connection viability, and reify
    sync_pair = network.pair(
        local_cx,
        src,
        target,
    )

    raise NotImplementedError


    # choose protocol
    sync_protocol = dict(_PROTOCOL_MAPS)[protocol]

    sync_pair.sync(
        local_cx,
        sync_protocol,
    )

if __name__ == "__main__":

    cli()
