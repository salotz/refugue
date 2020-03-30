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

# TODO: leads to circular imports for typechecking. Are we leading to
# header files or something!! Currently typechecking turned off
# from .image import (
#     Replica,
#     Image,
# )


__all__ = [
]


## Sync specs

@dc.dataclass
class SyncPolicy():
    """A protocol-agnostic specification of a desired synchronization
    between two replicas. This does not include things like working
    sets but rather behaviors for merging, updating, backups, one-way,
    two-way etc.

    Also doesn't include things like encryption or compression.

    """

    inject: bool
    clobber: bool
    clean: bool
    prune: bool

@dc.dataclass
class TransportPolicy():
    """Policy regarding details about how a transport should take place
    including encryption and compression."""

    compression: Optional[str]
    encryption: Optional[str]
    dry: bool
    backup: Optional[str]
    create: Optional[str]

@dc.dataclass
class SyncSpec():

    sync_pol: SyncPolicy
    transport_pol: TransportPolicy

@dc.dataclass
class SyncProtocol():
    """Abstract Base Class for SyncProtocols"""

    @classmethod
    def validate_sync_spec(cls,
                           sync_spec: SyncSpec,
    ):
        """Validate that the sync_spec is supported by this protocol."""

        NotImplemented

    @classmethod
    def gen_sync_func(cls,
                      cx: Context,
                      src, # : Replica,
                      target, # : Replica,
                      sync_spec: SyncSpec,
    ) -> Callable[[Context], None]:

        if not cls.validate_sync_spec(sync_spec):
            raise ValueError(f"Invalid SyncSpec for this protocol: {self.__name__}")

        NotImplemented



