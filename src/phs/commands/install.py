import getpass
from typing import Annotated

from cyclopts import Parameter

from phs.context import AppContext
from phs.execution.factory import ConnectionFactory


def install(
    hostname: str,
    *,
    userpassword: str | None = None,
    force: bool = False,
    context: Annotated[AppContext, Parameter(parse=False)],
):
    inventory = context.inventory_loader.load(hostname)

    disk_names = [disk.device for disk in inventory.host.disks]

    if not force:
        context.output.warning(
            f"This will ERASE the disks {', '.join(disk_names)} on {inventory.host.hostname}."
        )
        answer = context.output.prompt("Continue? [yes/N] ").strip().lower()
        if answer != "yes":
            context.output.info("Installation aborted.")
            return

    if userpassword is None:
        userpassword = getpass.getpass(f"Password for {inventory.host.username}: ")
        confirmation = getpass.getpass("Confirm password: ")

        if userpassword != confirmation:
            context.output.error("Passwords do not match.")
            return

    con = ConnectionFactory(inventory.host, context.settings)
    target = con.ssh("root")

    result = target.run("echo 'Hello World'")
    print(result.stdout)
