from collections.abc import Callable
from typing import Protocol

from backup.archive import Archive
from backup.reporter import Reporter


class TargetProtocol(Protocol):
    """Protocol defining the interface for backup targets."""

    label: str
    description: str

    def list_archives(self, label: str | None = None) -> list[Archive]: ...

    def transfer_archive(self, archive: Archive, dry: bool = False): ...

    def perform_thinning(
        self, label: str, thin_archives: Callable, dry: bool = False
    ): ...


class Target(Reporter, TargetProtocol):
    """Base class for all backup targets implementing the TargetProtocol."""
