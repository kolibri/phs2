import shlex
import subprocess
from dataclasses import dataclass
from typing import Protocol

from fabric import Connection


@dataclass(frozen=True, slots=True)
class CommandResult:
    stdout: str
    stderr: str
    returncode: int


class Target(Protocol):
    def run(
        self,
        command: str,
        *,
        sudo: bool = False,
    ) -> CommandResult: ...


class RemoteTarget:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def run(
        self,
        command: str,
        *,
        sudo: bool = False,
    ) -> CommandResult:
        if sudo:
            result = self.connection.sudo(command, warn=True)
        else:
            result = self.connection.run(command, warn=True)

        return CommandResult(
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.exited,
        )


class DryRunTarget:
    def __init__(self, target: Target) -> None:
        self.target = target

    def run(
        self,
        command: str,
        *,
        sudo: bool = False,
    ) -> CommandResult:
        prefix = "sudo " if sudo else ""

        return CommandResult(
            stdout=f"[dry-run] would execute: {prefix}{command}",
            stderr="",
            returncode=0,
        )


class ArchRootTarget:
    def __init__(self, target: Target, root: str) -> None:
        self.target = target
        self.root = root

    def run(
        self,
        command: str,
        *,
        sudo: bool = False,
    ) -> CommandResult:
        del sudo

        chroot_command = (
            f"arch-chroot {shlex.quote(self.root)} /bin/sh -c {shlex.quote(command)}"
        )

        return self.target.run(
            chroot_command,
            sudo=True,
        )


class LocalTarget:
    def run(
        self,
        command: str,
        *,
        sudo: bool = False,
    ) -> CommandResult:
        if sudo:
            argv = [
                "sudo",
                "/bin/sh",
                "-c",
                command,
            ]
        else:
            argv = [
                "/bin/sh",
                "-c",
                command,
            ]

        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            check=False,
        )

        return CommandResult(
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )
