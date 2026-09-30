from pathlib import Path
from typing import Any

from phs.inventory.data.recipe import Recipe
from phs.inventory.loader.operation import OperationLoaderRegistry


class RecipeLoader:
    def __init__(
        self,
        operation_loader: OperationLoaderRegistry,
    ):
        self._operation_loader = operation_loader

    def load(
        self,
        name: str,
        value: Any,
        source: Path,
    ) -> Recipe:
        if not isinstance(value, list):
            raise TypeError(f"{source}: recipe {name!r} must be a list")

        return Recipe(
            name=name,
            operations=self._operation_loader.load_many(
                value,
                str(source),
            ),
            source=source,
        )

    def load_many(
        self,
        value: Any,
        source: Path,
    ) -> dict[str, Recipe]:
        if not isinstance(value, dict):
            raise TypeError(f"{source}: recipes must be a mapping")

        recipes: dict[str, Recipe] = {}

        for name, recipe_value in value.items():
            if name in recipes:
                raise TypeError(f"{source}: recipe {name!r} defined twice")

            recipes[name] = self.load(
                name,
                recipe_value,
                source,
            )

        return recipes
