import logging
from pathlib import Path

from cyclopts import App

from phs.inventory.config import create_configuration_loader

logging.basicConfig(level=logging.INFO)

app = App()


@app.command
def install(hostname: str):
    loader = create_configuration_loader()

    configuration = loader.load(Path("tests/hostconfig"))

    print(configuration)

    """
    host = HostConfig('test', '127.0.0.1', 2202)

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

        add_op(
            state,
            pacman,
            name="say hello",
            commands=['echo "hello world"'],
        )

        run_ops(state)
    finally:
        disconnect_all(state)

    print(f"Provisioning {hostname}")
    """


if __name__ == "__main__":
    app()
