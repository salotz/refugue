import runpy
import dataclasses as dc
from pathlib import Path
from enum import Enum
from typing import (
    Optional,
    Union,
    Tuple,
    Mapping,
    Sequence,
)

CONFIG_FIELDS = (
    'ROOT_NAME',
    'HOST_NODE_ALIASES',
    'PEER_ALIASES',
    'PEER_TYPES',
    'PEERS',
    'PEER_MOUNT_PREFIXES',
    'PEER_MOUNTS',
    'CONNECTIONS',
    'DEFAULT_PEER_TYPE_REFINEMENTS',
    'DEFAULT_PEER_REFINEMENTS',
    'REPLICAS',
    'REFINEMENT_REPLICA_PREFIXES',
    'REPLICA_PREFIXES',
    'REPLICA_EXCLUDES',
    'REPLICA_INCLUDES',
)

@dc.dataclass
class Config():
    ROOT_NAME: str
    HOST_NODE_ALIASES: Mapping[str, Sequence[str]]
    PEER_ALIASES: Mappping[str, str]
    PEER_TYPES: Mapping[str, Sequence[str]]
    PEERS: Tuple[str]
    PEER_MOUNT_PREFIXES: Mapping[Tuple[str, str], str]
    PEER_MOUNTS: Mapping[Tuple[str, str], str]
    CONNECTIONS: Mapping[str, Mapping[str, str]]
    DEFAULT_PEER_TYPE_REFINEMENTS: Mapping[str, str]
    DEFAULT_PEER_REFINEMENTS: Mapping[str, str]
    REPLICAS: Sequence[str]
    REFINEMENT_REPLICA_PREFIXES: Mapping[str, str]
    REPLICA_PREFIXES: Mapping[str, str]
    REPLICA_EXCLUDES: Mapping[str, Union[Seqence[str], Ellipsis]]
    REPLICA_INCLUDES: Mapping[str, Union[Seqence[str], Ellipsis]]

def load_config(path):
    """Load a python formatted config file.

    Parameters
    ----------

    path : Path

    Returns
    -------

    config : Config obj

    """

    config_d = {key : value for key, value
                in runpy.from_path(path).items()
                if key in CONFIG_FIELDS}

    config = Config(**config_d)

    return config
