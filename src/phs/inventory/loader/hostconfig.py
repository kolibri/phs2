from pathlib import Path
from typing import Any

from pydantic import ValidationError

from phs.inventory.data.hostconfig import HostFile, HostSettings
from phs.inventory.data.operation import RecipeOperation
from phs.inventory.loader.operation import OperationLoaderRegistry
from phs.inventory.loader.recipe import RecipeLoader


class HostLoader:
    def __init__(
        self,
        operation_loader: OperationLoaderRegistry,
        recipe_loader: RecipeLoader,
    ):
        self._operation_loader = operation_loader
        self._recipe_loader = recipe_loader

    def load(
        self,
        data: dict[str, Any],
        source: Path,
        global_recipes: dict,
    ) -> HostFile:
        hostname = self._get_hostname(data, source)

        host_data = data[hostname]

        if not isinstance(host_data, dict):
            raise TypeError(f"{source}: host {hostname!r} must be a mapping")

        local_recipes = self._recipe_loader.load_many(
            data.get("recipes", {}),
            source,
        )

        self._check_recipe_collisions(
            local_recipes,
            global_recipes,
        )

        config = self._load_config(
            host_data.get("config", {}),
            source,
        )

        recipes = self._load_recipe_calls(
            host_data.get("recipes", []),
            source,
        )

        return HostFile(
            hostname=hostname,
            config=config,
            recipes=recipes,
            local_recipes=local_recipes,
            source=source,
        )

    @staticmethod
    def _get_hostname(
        data: dict[str, Any],
        source: Path,
    ) -> str:
        host_names = [key for key in data if key != "recipes"]

        if len(host_names) != 1:
            raise TypeError(f"{source}: expected exactly one host")

        return host_names[0]

    @staticmethod
    def _load_config(
        value: Any,
        source: Path,
    ) -> HostSettings:
        try:
            return HostSettings.model_validate(value)
        except ValidationError as exc:
            raise TypeError(f"{source}: invalid host config:\n{exc}") from exc

    def _load_recipe_calls(
        self,
        values: Any,
        source: Path,
    ) -> list[RecipeOperation]:
        if not isinstance(values, list):
            raise TypeError(f"{source}: host recipes must be a list")

        result = []

        for value in values:
            operation = self._operation_loader.load(
                {"recipe": value},
                str(source),
            )

            if not isinstance(operation, RecipeOperation):
                raise TypeError("Recipe loader returned unexpected operation")

            result.append(operation)

        return result

    @staticmethod
    def _check_recipe_collisions(
        local: dict,
        global_: dict,
    ) -> None:
        for name, recipe in local.items():
            if name in global_:
                raise TypeError(
                    f"Recipe {name!r} is defined both locally "
                    f"({recipe.source}) and globally "
                    f"({global_[name].source})"
                )
