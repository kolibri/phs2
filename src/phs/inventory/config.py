from typing import Any

import yaml
from pydantic import BaseModel, Field

from phs.inventory.recipe import Recipe


class ConnectionConfig(BaseModel):
    host: str
    port: int = 22


class MicrocodeConfig(BaseModel):
    package: str
    initrd: str


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


class RecipeInvocation(BaseModel):
    name: str
    variables: dict[str, Any] = Field(default_factory=dict)


class HostConfig(BaseModel):
    hostname: str
    username: str
    home: str | None = None
    connection: ConnectionConfig
    microcode: MicrocodeConfig | None = None
    base_packages: list[str] = Field(default_factory=list)
    disks: list[DiskConfig] = Field(default_factory=list)
    recipes: list[RecipeInvocation] = Field(default_factory=list)


class HostFile(BaseModel):
    host: HostConfig
    recipes: dict[str, Recipe] = Field(default_factory=dict)


def load_host(path: str) -> HostFile:
    with open(path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return HostFile.model_validate(_parse_host_recipe_invocations(data))


def _parse_host_recipe_invocations(data: dict) -> dict:
    """
    Convert:

        recipes:
          - default: {}
          - hyprland:
              config_dir: "..."

    into:

        recipes:
          - name: default
            variables: {}
          - name: hyprland
            variables:
              config_dir: "..."
    """

    host = data.get("host", {})
    recipes = host.get("recipes", [])

    parsed = []

    for recipe in recipes:
        if not isinstance(recipe, dict) or len(recipe) != 1:
            raise ValueError(
                "Each recipe invocation must contain exactly one recipe name"
            )

        name, variables = next(iter(recipe.items()))

        if variables is None:
            variables = {}

        if not isinstance(variables, dict):
            raise TypeError(f"Variables for recipe '{name}' must be a mapping")

        parsed.append(
            {
                "name": name,
                "variables": variables,
            }
        )

    host["recipes"] = parsed

    return data
