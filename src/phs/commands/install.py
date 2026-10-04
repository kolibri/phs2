import getpass
from typing import Annotated

from cyclopts import Parameter

from phs.context import AppContext


def install(
    hostname: str,
    *,
    userpassword: str | None = None,
    force: bool = False,
    context: Annotated[AppContext, Parameter(parse=False)],
):
    host_data = context.inventory.get_host(hostname)
    host_config = host_data.config
    disk_names = [disk.device for disk in host_config.disks]
    base_packages = [
        "base",
        "linux",
        "linux-firmware",
        "base-devel",
        "dialog",
        "openssh",
        "rsync",
        "zsh",
        "git",
        "python",
    ]
    base_packages.extend(host_config.base_packages)
    if host_config.microcode_package is not None:
        base_packages.append(host_config.microcode_package)

    if not force:
        context.output.warning(
            f"This will ERASE the disks {', '.join(disk_names)} on {host_data.hostname}."
        )
        answer = context.output.prompt("Continue? [yes/N] ").strip().lower()
        if answer != "yes":
            context.output.info("Installation aborted.")
            return

    if userpassword is None:
        userpassword = getpass.getpass(f"Password for {host_config.username}: ")
        confirmation = getpass.getpass("Confirm password: ")

        if userpassword != confirmation:
            context.output.error("Passwords do not match.")
            return
