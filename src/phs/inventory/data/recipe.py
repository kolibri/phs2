from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from phs.inventory.data.operation import Operation


class Recipe(BaseModel):
    name: str
    operations: list[Operation]
    source: Path
