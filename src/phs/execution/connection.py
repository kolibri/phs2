from pathlib import Path

from fabric import Connection

from phs.inventory.config import HostConfig
from phs.settings import Settings


def connect(host: HostConfig, settings: Settings) -> Connection:
    return Connection(
        host=host.connection.host,
        port=host.connection.port,
        user=host.username,
        connect_kwargs={
            "key_filename": str(Path(settings.sshkey).expanduser()),
        },
    )
