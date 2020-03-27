import runpy
import os.path as osp
from pathlib import Path
import runpy

import click
from invoke import Context

from .network import Network
from .image import Image
from .sync import SyncPair


DEFAULT_NETWORK_PATH = "$HOME/.config/refugue/network.config.py"

IMAGE_CONFIG_DIR = "$HOME/.config/refugue/images"
"""Location where image configs are expected"""

DEFAULT_IMAGE_CONF_NAME = "default.image.config.py"
"""Default image conf file to read"""

NETWORK_CONFIG_KEYS = (
    "HOSTS",
    "DRIVES",
    "PEER_ALIASES",
    "HOST_NODE_ALIASES",
    "PEER_TYPES",
    "PEERS",
    "PEER_MOUNT_PREFIX_TYPES",
    "CONNECTIONS",
)

IMAGE_CONFIG_KEYS = (
    "REPLICAS",
    "REPLICA_PREFIXES",
    "REPLICA_EXCLUDES",
    "REPLICA_INCLUDES",
)



def read_network_config(config_path):
    """Read a python code config file for a network spec and strip out
    only the recognized variables

    """

    config_all = runpy.run_path(str(config_path))

    config = {key : value for key, value in config_all.items()
              if key in NETWORK_CONFIG_KEYS}

    return config

def read_image_config(config_path):
    """Read a python code config file for an image spec and strip out only
    the recognized variables

    """

    config_all = runpy.run_path(str(config_path))

    config = {key : value for key, value in config_all.items()
              if key in IMAGE_CONFIG_KEYS}

    return config

@click.command()
@click.option("--network", type=click.Path(exists=True), default=None)
@click.option("--image", type=click.Path(exists=True), default=None)
@click.option("--transport", default=None)
@click.option("--protocol", default=None)
@click.argument("src")
@click.argument("target")
def cli(network, image, transport, protocol, src, target):

    ## Load the config files

    if network is None:
        network = DEFAULT_NETWORK_PATH

    if image is None:
        image = Path(IMAGE_CONFIG_DIR) / DEFAULT_IMAGE_CONF_NAME

    # expand shell variables to the config files
    network_path = Path(osp.expanduser(osp.expandvars(network)))
    image_path = Path(osp.expanduser(osp.expandvars(image)))

    network_config_d = read_network_config(network_path)
    image_config_d = read_image_config(image_path)

    ## Network

    # build the network from the configuration file
    network = Network.from_config(network_config_d)

    ## Image & Replicas

    # then embed it into the Image along with the image spec with all
    # the replicas
    image = Image.from_config(image_config_d, network)

    ## Sync Protocol

    # The local execution context
    local_cx = Context()

    # identify the replicas in the network, discover current network
    # topology, validate connection viability, and reify
    sync_pair = image.pair(
        local_cx,
        src,
        target,
    )

    raise NotImplementedError

    ## Transport and Execution

    # choose protocol
    sync_protocol = dict(_PROTOCOL_MAPS)[protocol]

    sync_pair.sync(
        local_cx,
        sync_protocol,
    )

if __name__ == "__main__":

    cli()
