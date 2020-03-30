import runpy
import os.path as osp
from pathlib import Path
import runpy

import click
from invoke import Context

from .network import Network
from .image import Image
from .sync import (
    SyncPolicy,
    TransportPolicy,
    SyncSpec,
)
from .protocols.rsync import RsyncProtocol


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


_PROTOCOL_MAPS = (
    ('rsync', RsyncProtocol),
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


from invoke.vendor.six.moves import input

def confirm(question, assume_yes=True):
    """
    Ask user a yes/no question and return their response as a boolean.
    ``question`` should be a simple, grammatically complete question such as
    "Do you wish to continue?", and will have a string similar to ``" [Y/n] "``
    appended automatically. This function will *not* append a question mark for
    you.
    By default, when the user presses Enter without typing anything, "yes" is
    assumed. This can be changed by specifying ``assume_yes=False``.
    .. note::
        If the user does not supplies input that is (case-insensitively) equal
        to "y", "yes", "n" or "no", they will be re-prompted until they do.
    :param str question: The question part of the prompt.
    :param bool assume_yes:
        Whether to assume the affirmative answer by default. Default value:
        ``True``.
    :returns: A `bool`.
    """
    # Set up suffix
    if assume_yes:
        suffix = "Y/n"
    else:
        suffix = "y/N"
    # Loop till we get something we like
    # TODO: maybe don't do this? It can be annoying. Turn into 'q'-for-quit?
    while True:
        # TODO: ensure that this is Ctrl-C friendly, ISTR issues with
        # raw_input/input on some Python versions blocking KeyboardInterrupt.
        response = input("{0} [{1}] ".format(question, suffix))
        response = response.lower().strip()  # Normalize
        # Default
        if not response:
            return assume_yes
        # Yes
        if response in ["y", "yes"]:
            return True
        # No
        if response in ["n", "no"]:
            return False
        # Didn't get empty, yes or no, so complain and loop
        err = "I didn't understand you. Please specify '(y)es' or '(n)o'."
        print(err, file=sys.stderr)


@click.command()
@click.option("--network", type=click.Path(exists=True), default=None)
@click.option("--image", type=click.Path(exists=True), default=None)
@click.option("--transport", default=None)
@click.option("--protocol", default='rsync')
@click.option("--create", is_flag=True, default=True, help="Create the target if doesn't exist")
@click.option("--yes", '-y', is_flag=True, default=False)
@click.argument("src")
@click.argument("target")
def cli(network, image, transport, protocol, create, yes, src, target):

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

    ## Generate the SyncSpec from transport and sync policies

    # STUB: for now we just have this static for testing
    sync_pol = SyncPolicy(
        dry = True,
        safe = True,
        ow_sync = False,
        clean = False,
        force = False,
    )
    transport_pol = TransportPolicy(
        compress = False,
        encrypt = False,
    )
    sync_spec = SyncSpec(
        sync_pol = sync_pol,
        transport_pol = transport_pol,
    )

    ## Sync Protocol

    # The local execution context
    local_cx = Context()

    # identify the replicas in the network, discover current network
    # topology, validate connection viability, and reify
    sync_pair = image.pair(
        local_cx,
        sync_spec,
        src,
        target,
    )

    ## Transport and Execution

    # choose protocol
    sync_protocol = dict(_PROTOCOL_MAPS)[protocol]

    # get the context and function to execute
    ex_cx, sync_func, confirm_message = sync_pair.sync(
        local_cx,
        sync_protocol,
    )

    src_conn = image.network.resolve_peer_connection(sync_pair.src.peer)

    if src_conn is None:
        src_conn = "localhost"

    else:
        src_conn = f"{src_conn['user']}@{src_conn['host']}"

    # the create command if asked for
    if create:
        target_replica_path = image.resolve_replica_path(
            local_cx,
            sync_pair.target,
        )

        create_command = f"mkdir -p {target_replica_path}"

    # confirm this is okay to run
    print("The generated command:\n")

    if create:
        print(create_command)

    print(confirm_message)

    # get confirmation if not already
    if not yes:
        yes = confirm(
            f"Run this command on the host: '{sync_pair.src.peer.name}' via '{src_conn}'?",
            assume_yes=False,
        )

    if yes:

        print(f"Running command on host: '{sync_pair.src.peer.name}' via connection: '{src_conn}'")
        ex_cx.run(create_command)
        sync_func(ex_cx)

    else:
        print("Command Cancelled")


if __name__ == "__main__":

    cli()
