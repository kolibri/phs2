from pathlib import Path
import logging
from cyclopts import App
from pyinfra.api import Inventory, Config, State
from pyinfra.api.connect import connect_all, disconnect_all
from pyinfra.api.operation import add_op
from pyinfra.api.operations import run_ops
from pyinfra.operations import server

from phs.inventory.host import Host


logging.basicConfig(level=logging.INFO)

app = App()


@app.command
def install(hostname: str):
    host = Host('test', '127.0.0.1', 2202)

    inventory = Inventory((["127.0.0.1"], {
        "ssh_user": "root",
        "ssh_port": 2202,
        "ssh_key": str(Path.cwd() / "tests/vm/helper/files/id_ed25519"),

    }))
    
    config = Config()

    state = State(inventory, config)

    try:
        connect_all(state)

        add_op(
            state,
            server.shell,
            name="say hello",
            commands=['echo "hello world"'],
        )

        run_ops(state)
    finally:
        disconnect_all(state)

    print(f"Provisioning {hostname}")


if __name__ == "__main__":
    app()
