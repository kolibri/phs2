from __future__ import annotations

from typing import Any, Protocol

from phs.inventory.data.operation import (
    DirOperation,
    FileOperation,
    Operation,
    PackageOperation,
    RecipeOperation,
    RepoOperation,
)


class OperationLoader(Protocol):
    operation_type: str

    def load(
        self,
        config: Any,
        source: str,
    ) -> Operation: ...


class OperationLoaderRegistry:
    def __init__(
        self,
        loaders: list[OperationLoader],
    ):
        self._loaders: dict[str, OperationLoader] = {}

        for loader in loaders:
            if loader.operation_type in self._loaders:
                raise TypeError(
                    f"Duplicate operation loader: {loader.operation_type!r}"
                )

            self._loaders[loader.operation_type] = loader

    def load(
        self,
        value: Any,
        source: str,
    ) -> Operation:
        if not isinstance(value, dict) or len(value) != 1:
            raise TypeError(
                f"{source}: operation must contain exactly one type: {value!r}"
            )

        operation_type, config = next(iter(value.items()))

        try:
            loader = self._loaders[operation_type]
        except KeyError:
            raise TypeError(f"{source}: unknown operation {operation_type!r}") from None

        return loader.load(config, source)

    def load_many(
        self,
        values: list[Any],
        source: str,
    ) -> list[Operation]:
        return [self.load(value, source) for value in values]


class PackageOperationLoader:
    operation_type = "package"

    def load(
        self,
        config: Any,
        source: str,
    ) -> PackageOperation:
        return PackageOperation(
            type=self.operation_type,
            packages=config,
        )


class RepoOperationLoader:
    operation_type = "repo"

    def load(
        self,
        config: Any,
        source: str,
    ) -> RepoOperation:
        if not isinstance(config, dict):
            raise TypeError(f"{source}: repo must be a mapping")

        return RepoOperation(
            type=self.operation_type,
            **config,
        )


class FileOperationLoader:
    operation_type = "file"

    def load(
        self,
        config: Any,
        source: str,
    ) -> FileOperation:
        if not isinstance(config, dict):
            raise TypeError(f"{source}: file must be a mapping")

        return FileOperation(
            type=self.operation_type,
            **config,
        )


class DirOperationLoader:
    operation_type = "dir"

    def load(
        self,
        config: Any,
        source: str,
    ) -> DirOperation:
        if not isinstance(config, dict):
            raise TypeError(f"{source}: dir must be a mapping")

        return DirOperation(
            type=self.operation_type,
            **config,
        )


class RecipeOperationLoader:
    operation_type = "recipe"

    def load(
        self,
        config: Any,
        source: str,
    ) -> RecipeOperation:
        if not isinstance(config, dict) or len(config) != 1:
            raise TypeError(
                f"{source}: recipe must be a mapping containing exactly one recipe name"
            )

        name, args = next(iter(config.items()))

        if not isinstance(name, str):
            raise TypeError(f"{source}: recipe name must be a string")

        if args is None:
            args = {}

        if not isinstance(args, dict):
            raise TypeError(
                f"{source}: arguments for recipe {name!r} must be a mapping"
            )

        return RecipeOperation(
            type=self.operation_type,
            name=name,
            args=args,
        )
