from pathlib import Path

from fabric import Connection

from phs.execution.connection import connect
from phs.execution.target import ArchRootTarget, DryRunTarget, RemoteTarget, Target
from phs.inventory.config import HostConfig
from phs.settings import Settings


def target_for_host(
    host: HostConfig,
    settings: Settings,
    *,
    arch_root: str | None = None,
) -> Target:
    target: Target = RemoteTarget(connect(host, settings))

    if settings.dry_run:
        target = DryRunTarget(target)

    if arch_root is not None:
        target = ArchRootTarget(target, arch_root)

    return target


class ConnectionFactory:
    def __init__(self, host: HostConfig, settings: Settings) -> None:
        self.host = host
        self.settings = settings

    def ssh(self, username: str | None = None) -> RemoteTarget:
        return RemoteTarget(self._connection(username))

    def dry_run(self, username: str | None = None):
        return DryRunTarget(self.ssh(username))

    def arch_chroot(self, username: str | None = None, mount_point: str = "/mnt"):
        return ArchRootTarget(self.ssh(username), mount_point)

    def _connection(self, username: str | None = None) -> Connection:
        if username is None:
            username = self.host.username
        return Connection(
            host=self.host.connection.host,
            port=self.host.connection.port,
            user=username,
            connect_kwargs={
                "key_filename": str(Path(self.settings.sshkey).expanduser()),
            },
        )
