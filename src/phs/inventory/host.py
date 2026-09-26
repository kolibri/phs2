from dataclasses import dataclass


@dataclass(frozen=True)
class Host:
    name: str
    hostname: str
    ssh_port: int