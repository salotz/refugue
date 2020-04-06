import runpy
import os.path as osp
from pathlib import Path
import runpy

import click
from invoke import Context
import toml

from refugue.network import (
    Network,
    RefugueNetworkError,
    LocalConnection,
    ImpossibleConnection,
    SSHConnection,
)
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

DEFAULT_CONFIG_PATH = "$HOME/.config/refugue/config.toml"
"""Default path for the configuration file that configures the
behavior of the refugue tool."""


DEFAULT_BACKUP_DIR = "$HOME/.local/share/refugue/backups"
"""Default location for refile backups to be placed."""

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
    "DEFAULT_PAIR_OPTIONS",
    "PAIR_OPTIONS",
)

SYNC_OPTIONS = (
    ('i', 'inject',),
    ('k', 'clobber',),
    ('c', 'clean',),
    ('p', 'prune',),
)

DEFAULT_SYNC_OPTIONS = (
    ('inject', False),
    ('clobber', False),
    ('clean', True),
    ('prune', False),
)

DEFAULT_TRANSPORT_OPTIONS = (
    ('backup', 'rename'),
    ('compression', 'auto'),
    ('encryption', None),
    ('create', True),
)


BACKUP_METHODS = (
    # don't backup
    None,

    # backup by renaming the file with a refugue specific suffix:
    # '*.refugue-backup'
    'rename',

    # move to the configured backup refiling location, default:
    # '$HOME/.local/share/refugue/backups/YYY-MM-DD:min-sec'
    # TODO: implement
    # 'refile',
)

COMPRESSION_METHODS = (
    None,
    # choose based on whether it is between two hosts that are remote
    # to each other using the default mechanism
    'auto',

    # default 'on' method
    'rsync',

    # TODO
    # 'blosc',
    # 'bzip2',
    # 'zlib',
)

ENVRYPTION_METHODS = (
    None,
    # TODO
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
@click.option("--network",
              type=click.Path(exists=True),
              default=None,
              help="Network specification file to use.")
@click.option("--image",
              type=click.Path(exists=True),
              default=None,
              help="Image specification file to use.")
@click.option("--subtree",
              default=None,
              help="Subtree to restrict sync of image to. Relative path to root of replica.")
@click.option("--sync",
              default=None,
              help="Comma separated list of sync policy flags to use or None, "
              "overrides default from image config, "
              "e.g. 'clobber,clean,prune' or 'k,c,p'. "
              "Default='clean'")
@click.option("--dry",
              is_flag=True,
              default=False,
              help="Run as a dry run if the transport protocol supports it")
@click.option("--create",
              is_flag=True,
              default=True,
              help="Create the target if doesn't exist")
@click.option("--backup",
              default='rename',
              help="Choose a backup method: None or 'rename'")
@click.option("--compression",
              default=None,
              help="Choose a compression method: None, 'auto', 'rsync'")
@click.option("--encryption",
              default=None,
              help="Choose an encryption method: None")
@click.option("--yes",
              '-y',
              is_flag=True,
              default=False,
              help="Don't ask for confirmation")
@click.argument("src")
@click.argument("target")
def cli(
        # file-based specifications
        network, image, subtree,
        # sync spec overrides from image
        sync,
        # transport options
        dry, create, backup, compression, encryption,
        # other CLI options
        yes,
        # the alpha and beta pair
        src, target):

    ### Load the config files

    if network is None:
        network = DEFAULT_NETWORK_PATH

    if image is None:
        image = Path(IMAGE_CONFIG_DIR) / DEFAULT_IMAGE_CONF_NAME

    # expand shell variables to the config files
    network_path = Path(osp.expanduser(osp.expandvars(network)))
    image_path = Path(osp.expanduser(osp.expandvars(image)))

    network_config_d = read_network_config(network_path)
    image_config_d = read_image_config(image_path)

    ### Network

    # build the network from the configuration file
    network = Network.from_config(network_config_d)

    ### Image & Replicas

    # then embed it into the Image along with the image spec with all
    # the replicas
    image = Image.from_config(image_config_d, network)

    ### Generate the SyncSpec from transport and sync policies

    ## sync options

    # if command line sync was given use that
    if sync is not None:

        # the possible names
        sync_names = [opt for _, opt in SYNC_OPTIONS]
        sync_abbrevs = [abbrev for abbrev, _ in SYNC_OPTIONS]

        # initialize
        sync_spec = {opt : False for opt in sync_names}

        # parse
        sync_opts = {}
        if sync.strip() != '':
            sync_opts = sync.strip().split(',')

        # turn them on that are given in the string
        for opt in sync_opts:

            # get the full name if necessary
            if opt in sync_abbrevs:
                opt = sync_names[sync_abbrevs.index(opt)]

            sync_spec[opt] = True

    # otherwise we want to load from the image config the pairs if
    # given, and if not using the safe deafult
    else:

        # start with the default
        sync_spec = dict(DEFAULT_SYNC_OPTIONS)

        # use the default from the config file
        if 'DEFAULT_PAIR_OPTIONS' in image_config_d:
            sync_spec.update(image_config_d['DEFAULT_PAIR_OPTIONS']['sync'])

        # then update with the options in the specific pairing

        # choose which pairing keys to try given the src and target
        pairing_keys = [
            (src, target, '-->'),
            (src, target, '<-->'),
            (target, src, '<-->'),
        ]

        for key in pairing_keys:
            if key in image_config_d['PAIR_OPTIONS']:
                pair_spec = image_config_d['PAIR_OPTIONS'][key]
                sync_spec.update(image_config_d['PAIR_OPTIONS'][key]['sync'])
                break

    ## Transport


    transport_spec = dict(DEFAULT_TRANSPORT_OPTIONS)

    # use the default from the config file
    if 'DEFAULT_PAIR_OPTIONS' in image_config_d:
        transport_spec.update(image_config_d['DEFAULT_PAIR_OPTIONS']['transport'])

    # then update with the options in the specific pairing

    # choose which pairing keys to try given the src and target
    pairing_keys = [
        (src, target, '-->'),
        (src, target, '<-->'),
        (target, src, '<-->'),
    ]

    for key in pairing_keys:
        if key in image_config_d['PAIR_OPTIONS']:
            pair_spec = image_config_d['PAIR_OPTIONS'][key]
            transport_spec.update(image_config_d['PAIR_OPTIONS'][key]['transport'])
            break

    # finally override with command line options
    cli_transport_spec = {
        'dry' : dry,
        'create' : create,
        'backup' : backup,
        'compression' : compression,
        'encryption' : encryption,
    }

    transport_spec.update(cli_transport_spec)

    # create them
    sync_pol = SyncPolicy(**sync_spec)

    transport_pol = TransportPolicy(**transport_spec)

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
        subtree,
        src,
        target,
    )

    ### Execution

    # STUB: choose protocol, its always rsync now
    sync_protocol = RsyncProtocol

    # get the context and function to execute
    sync_func, confirm_message = sync_pair.sync(
        local_cx,
        sync_protocol,
    )

    # get the connections and contexts
    src_conn = image.network.resolve_peer_connection(sync_pair.src.peer)
    target_conn = image.network.resolve_peer_connection(sync_pair.src.peer)

    src_cx = image.network.resolve_peer_context(local_cx, sync_pair.src.peer)
    target_cx = image.network.resolve_peer_context(local_cx, sync_pair.target.peer)



    if issubclass(type(src_conn), LocalConnection):
        src_conn = "localhost"

    elif issubclass(type(src_conn), SSHConnection):
        src_conn = f"{src_conn.user}@{src_conn.host}"

    elif issubclass(type(src_conn), ImpossibleConnection):

        raise RefugueNetworkError("")

    # the create command if asked for
    if create:

        # get the path to create on that context
        target_replica_path = image.resolve_replica_path(
            local_cx,
            sync_pair.target,
        )

        # the command
        create_command = f"mkdir -p {target_replica_path}"


        # Preparation commands to run
        print("\nTarget Peer preparation commands:")
        print("--------------------------------------------------------------------------------")
        print(create_command)
        print("--------------------------------------------------------------------------------")

    # confirm this is okay to run
    print("\nThe generated command:")
    print("--------------------------------------------------------------------------------")
    print(confirm_message)
    print("--------------------------------------------------------------------------------")

    # get confirmation if not already
    if not yes:

        yes = confirm(
            f"Run this command on the host: '{sync_pair.src.peer.name}' via '{src_conn}'?",
            assume_yes=False,
        )

    if yes:

        # Create if necessary
        if create:
            print(f"Running preparation command on target host:")
            print("--------------------------------------------------------------------------------")
            target_cx.run(create_command)
            print("--------------------------------------------------------------------------------")

        print(f"Running command on source host: '{sync_pair.src.peer.name}' "
              "via connection: '{src_conn}'")
        print("Command Output:")
        print("--------------------------------------------------------------------------------")

        #### SYNC
        sync_func(local_cx, src_cx, target_cx)
        print("--------------------------------------------------------------------------------")
        print("Refugue says: Synchronization Finished")

    else:
        print("Command Cancelled")


if __name__ == "__main__":

    cli()
