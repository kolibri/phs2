from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from phs.inventory.data.operation import RecipeOperation
from phs.inventory.data.recipe import Recipe


class SshConfig(BaseModel):
    user: str
    port: int = 22


class PartitionConfig(BaseModel):
    name: str
    size: str
    filesystem: str | None = None
    mount: str | None = None
    type: str | None = None


class DiskConfig(BaseModel):
    device: str
    table: str
    partitions: list[PartitionConfig]


class HostSettings(BaseModel):
    ssh: SshConfig
    discs: list[DiskConfig] = Field(default_factory=list)


class HostFile(BaseModel):
    hostname: str
    config: HostSettings
    recipes: list[RecipeOperation]
    local_recipes: dict[str, Recipe]
    source: Path


class Configuration(BaseModel):
    hosts: list[HostFile]
    global_recipes: dict[str, Recipe]
