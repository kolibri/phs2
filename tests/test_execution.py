from dataclasses import dataclass, field

from phs.execution import (
    ArchRootTarget,
    DryRunTarget,
    FileTask,
    PackageTask,
)


@dataclass
class FakeTarget:
    installed: set[str] = field(default_factory=set)
    files: dict[str, str] = field(default_factory=dict)
    commands: list[tuple[str, bool, bool]] = field(default_factory=list)

    def run(
        self,
        command: str,
        *,
        sudo: bool = False,
        mutate: bool = False,
    ):
        self.commands.append((command, sudo, mutate))

        if command.startswith("pacman -Q -- "):
            package = command.removeprefix("pacman -Q -- ").strip("'\"")
            return type(
                "Result",
                (),
                {
                    "stdout": "",
                    "stderr": "",
                    "returncode": 0 if package in self.installed else 1,
                },
            )()

        if command.startswith("cat -- "):
            path = command.removeprefix("cat -- ").strip("'\"")
            if path not in self.files:
                return type(
                    "Result",
                    (),
                    {
                        "stdout": "",
                        "stderr": "",
                        "returncode": 1,
                    },
                )()

            return type(
                "Result",
                (),
                {
                    "stdout": self.files[path],
                    "stderr": "",
                    "returncode": 0,
                },
            )()

        return type(
            "Result",
            (),
            {
                "stdout": "",
                "stderr": "",
                "returncode": 0,
            },
        )()


def test_package_task_reports_missing_packages(capsys):
    target = FakeTarget(installed={"obsidian"})

    PackageTask(["firefox", "obsidian"]).execute(target)

    output = capsys.readouterr().out

    assert "I will install firefox" in output
    assert "obsidian is already installed" in output
    assert any("pacman -S" in command for command, _, _ in target.commands)


def test_dry_run_still_inspects_remote_state(capsys):
    remote = FakeTarget(installed={"obsidian"})
    target = DryRunTarget(remote)

    PackageTask(["firefox", "obsidian"]).execute(target)

    output = capsys.readouterr().out

    assert "I will install firefox" in output
    assert "obsidian is already installed" in output
    assert any(
        command.startswith("pacman -Q")
        for command, _, mutate in remote.commands
        if not mutate
    )
    assert not any(mutate for _, _, mutate in remote.commands)
    assert "[dry-run] would execute:" in output


def test_file_task_shows_diff_and_dry_run_does_not_write(capsys):
    remote = FakeTarget(files={"/etc/example.conf": "old=true\n"})
    target = DryRunTarget(remote)

    FileTask("/etc/example.conf", "old=false\n", sudo=True).execute(target)

    output = capsys.readouterr().out

    assert "-old=true" in output
    assert "+old=false" in output
    assert "[dry-run] would execute:" in output
    assert not any(mutate for _, _, mutate in remote.commands)


def test_arch_root_wraps_commands():
    remote = FakeTarget()
    target = ArchRootTarget(remote, "/mnt")

    target.run("pacman -Q -- firefox", sudo=False, mutate=False)

    command, sudo, mutate = remote.commands[0]
    assert command == "arch-chroot /mnt /bin/sh -c 'pacman -Q -- firefox'"
    assert sudo is True
    assert mutate is False
