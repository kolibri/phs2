import base64
import difflib
import shlex
from dataclasses import dataclass

from phs.execution.target import Target


@dataclass(frozen=True, slots=True)
class CommandTask:
    command: str
    sudo: bool = False

    def execute(self, target: Target) -> None:
        target.run(
            self.command,
            sudo=self.sudo,
            mutate=True,
        )


@dataclass(frozen=True, slots=True)
class PackageTask:
    packages: tuple[str, ...]

    def __init__(self, packages: str | list[str] | tuple[str, ...]) -> None:
        if isinstance(packages, str):
            packages = (packages,)
        else:
            packages = tuple(packages)

        if not packages:
            raise ValueError("PackageTask requires at least one package")

        object.__setattr__(self, "packages", packages)

    def execute(self, target: Target) -> None:
        missing: list[str] = []

        for package in self.packages:
            result = target.run(
                f"pacman -Q -- {shlex.quote(package)}",
                sudo=True,
                mutate=False,
            )

            if result.returncode != 0:
                missing.append(package)
            else:
                print(f"{package} is already installed")

        if not missing:
            return

        for package in missing:
            print(f"I will install {package}")

        packages = " ".join(shlex.quote(package) for package in missing)
        target.run(
            f"pacman -S --needed --noconfirm {packages}",
            sudo=True,
            mutate=True,
        )


@dataclass(frozen=True, slots=True)
class FileTask:
    path: str
    content: str
    sudo: bool = False

    def execute(self, target: Target) -> None:
        result = target.run(
            f"cat -- {shlex.quote(self.path)}",
            sudo=self.sudo,
            mutate=False,
        )

        if result.returncode == 0:
            current = result.stdout
            old = current.splitlines(keepends=True)
        elif result.returncode == 1:
            current = None
            old = []
        else:
            raise RuntimeError(
                f"Could not read {self.path}: {result.stderr.strip()}"
            )

        desired = self.content
        if desired and not desired.endswith("\n"):
            desired += "\n"

        if current == desired:
            return

        diff = difflib.unified_diff(
            old,
            desired.splitlines(keepends=True),
            fromfile=f"{self.path} (current)",
            tofile=f"{self.path} (desired)",
        )
        print("".join(diff), end="")

        encoded = base64.b64encode(desired.encode()).decode()
        command = (
            f"mkdir -p -- {shlex.quote(self.path.rsplit('/', 1)[0] or '.')}"
            f" && printf %s {shlex.quote(encoded)}"
            f" | base64 -d > {shlex.quote(self.path)}"
        )
        target.run(
            command,
            sudo=self.sudo,
            mutate=True,
        )
