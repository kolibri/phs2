from pathlib import Path
from typing import Any

import yaml

from phs.inventory.loader.hostconfig import HostLoader
from phs.inventory.loader.recipe import RecipeLoader

from .data.hostconfig import Configuration
from .loader.operation import (
    DirOperationLoader,
    FileOperationLoader,
    OperationLoaderRegistry,
    PackageOperationLoader,
    RecipeOperationLoader,
    RepoOperationLoader,
)


class YamlLoader:
    def load(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            return {}

        if not isinstance(data, dict):
            raise TypeError(f"{path}: top-level value must be a mapping")

        return data


class ConfigurationLoader:
    def __init__(
        self,
        yaml_loader: YamlLoader,
        recipe_loader: RecipeLoader,
        host_loader: HostLoader,
    ):
        self._yaml_loader = yaml_loader
        self._recipe_loader = recipe_loader
        self._host_loader = host_loader

    def load(
        self,
        config_dir: Path,
    ) -> Configuration:
        recipes = self._load_global_recipes(config_dir / "recipes")

        hosts = self._load_hosts(
            config_dir / "hosts",
            recipes,
        )

        return Configuration(
            hosts=hosts,
            global_recipes=recipes,
        )

    def _load_global_recipes(
        self,
        directory: Path,
    ) -> dict:
        result = {}

        for path in sorted(directory.glob("*.yaml")):
            data = self._yaml_loader.load(path)

            recipes = self._recipe_loader.load_many(
                data.get("recipes", {}),
                path,
            )

            for name, recipe in recipes.items():
                if name in result:
                    raise TypeError(
                        f"Recipe {name!r} is defined in both "
                        f"{result[name].source} and {recipe.source}"
                    )

                result[name] = recipe

        return result

    def _load_hosts(
        self,
        directory: Path,
        global_recipes: dict,
    ) -> list:
        result = []

        for path in sorted(directory.glob("*.yaml")):
            data = self._yaml_loader.load(path)

            result.append(
                self._host_loader.load(
                    data,
                    path,
                    global_recipes,
                )
            )

        return result


def create_configuration_loader() -> ConfigurationLoader:
    operation_loader = OperationLoaderRegistry(
        [
            PackageOperationLoader(),
            RepoOperationLoader(),
            FileOperationLoader(),
            DirOperationLoader(),
            RecipeOperationLoader(),
        ]
    )

    recipe_loader = RecipeLoader(
        operation_loader=operation_loader,
    )

    host_loader = HostLoader(
        operation_loader=operation_loader,
        recipe_loader=recipe_loader,
    )

    return ConfigurationLoader(
        yaml_loader=YamlLoader(),
        recipe_loader=recipe_loader,
        host_loader=host_loader,
    )
