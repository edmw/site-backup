"""
Base protocol for backup sources.

This module defines the common interface that all backup sources must implement.
"""

from pathlib import Path
from typing import Protocol, TypedDict, runtime_checkable

from backup.reporter import Reporter
from backup.utils import formatkv


class SourceConfig(TypedDict, total=False):
    """Configuration parameters for source instances."""

    dbname: str
    dbhost: str
    dbport: int
    dbuser: str
    dbpass: str
    dbprefix: str


@runtime_checkable
class SourceProtocol(Protocol):
    """Protocol defining the interface for backup sources."""

    fspath: Path
    fsconfig: Path

    title: str | None
    slug: str | None
    description: str
    email: str | None

    dbname: str | None
    dbhost: str | None
    dbport: int
    dbuser: str | None
    dbpass: str | None
    dbprefix: str | None
    dbcharset: str

    def __str__(self) -> str: ...


class BaseSource(Reporter, SourceProtocol):
    """Base class for all backup sources implementing the SourceProtocol."""

    def __init__(self, fspath: Path, fsconfig: Path) -> None:
        super().__init__()

        self.fspath = fspath
        self.fsconfig = fsconfig

        self.title = None
        self.slug = None
        self.description = ""
        self.email = None

        self.dbname = None
        self.dbhost = None
        self.dbport = 3306
        self.dbuser = None
        self.dbpass = None
        self.dbprefix = None
        self.dbcharset = "utf8mb4"

    def __str__(self) -> str:
        return formatkv(
            [
                ("Slug", self.slug),
                ("WP(Title)", self.title),
                ("WP(Email)", self.email),
                ("DB(Name)", self.dbname),
                ("DB(Host)", self.dbhost),
                ("DB(Port)", self.dbport),
                ("DB(Prefix)", self.dbprefix),
                ("DB(User)", self.dbuser),
                ("DB(Pass)", "*******" if self.dbpass else "-"),
            ],
            title=self.__class__.__name__.upper(),
        )
