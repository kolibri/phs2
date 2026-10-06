import logging
from dataclasses import replace
from typing import Annotated

from cyclopts import App, Parameter
from rich.console import Console

from phs.commands.install import install
from phs.commands.test import test
from phs.context import AppContext
from phs.inventory.loader import InventoryLoader
from phs.output import RichOutput
from phs.settings import Settings

console = Console()
_DEFAULT_SETTINGS = Settings()
app = App(
    console=console,
)

app.command(install)
app.command(test)

# logging.basicConfig(
#    level=logging.DEBUG,
#    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
# )


@app.meta.default
def main(
    *tokens: Annotated[
        str,
        Parameter(show=False, allow_leading_hyphen=True),
    ],
    settings: Settings = _DEFAULT_SETTINGS,
):
    settings = replace(
        settings,
        config_dir=settings.config_dir.expanduser(),
        sshkey=settings.sshkey.expanduser(),
    )

    inventory_loader = InventoryLoader(settings.config_dir)

    context = AppContext(
        output=RichOutput(console), settings=settings, inventory_loader=inventory_loader
    )

    command, bound, ignored = app.parse_args(tokens)

    additional_kwargs: dict[str, object] = {}

    if "context" in ignored:
        additional_kwargs["context"] = context

    try:
        return command(
            *bound.args,
            **bound.kwargs,
            **additional_kwargs,
        )
    except TypeError as error:
        context.output.error(str(error))
        raise SystemExit(1) from None


def run():
    app.meta()
