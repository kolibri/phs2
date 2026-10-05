from dataclasses import dataclass

from phs.inventory.loader import InventoryLoader
from phs.output import Output
from phs.settings import Settings


@dataclass(frozen=True, slots=True)
class AppContext:
    output: Output
    settings: Settings
    inventory_loader: InventoryLoader
