from phs.execution.connection import connect
from phs.execution.factory import target_for_host
from phs.execution.target import (
    ArchRootTarget,
    CommandResult,
    DryRunTarget,
    RemoteTarget,
    Target,
)
from phs.execution.tasks import CommandTask, FileTask, PackageTask

__all__ = [
    "ArchRootTarget",
    "CommandResult",
    "CommandTask",
    "DryRunTarget",
    "FileTask",
    "PackageTask",
    "RemoteTarget",
    "Target",
    "connect",
    "target_for_host",
]
