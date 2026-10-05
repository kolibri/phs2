import shlex
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
        mutate: bool = False,
    ) -> CommandResult: ...


class RemoteTarget:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def run(
        self,
        command: str,
        *,
        sudo: bool = False,
        mutate: bool = False,
    ) -> CommandResult:
        del mutate

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
        mutate: bool = False,
    ) -> CommandResult:
        if not mutate:
            return self.target.run(
                command,
                sudo=sudo,
                mutate=False,
            )

        prefix = "sudo " if sudo else ""
        print(f"[dry-run] would execute: {prefix}{command}")
        return CommandResult(stdout="", stderr="", returncode=0)


class ArchRootTarget:
    def __init__(self, target: Target, root: str) -> None:
        self.target = target
        self.root = root

    def run(
        self,
        command: str,
        *,
        sudo: bool = False,
        mutate: bool = False,
    ) -> CommandResult:
        del sudo

        chroot_command = (
            f"arch-chroot {shlex.quote(self.root)} /bin/sh -c {shlex.quote(command)}"
        )

        return self.target.run(
            chroot_command,
            sudo=True,
            mutate=mutate,
        )
