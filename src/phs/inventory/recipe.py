from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from phs.inventory.tasks import BaseTaskConfig, _parse_task


class Recipe(BaseModel):
    name: str | None = None
    vars: dict[str, Any] = Field(default_factory=dict)
    tasks: list[BaseTaskConfig] = Field(default_factory=list)

    @field_validator("tasks", mode="before")
    @classmethod
    def parse_tasks(cls, value: Any) -> list[BaseTaskConfig]:
        if value is None:
            return []

        if not isinstance(value, list):
            raise TypeError("Recipe tasks must be a list")

        return [_parse_task(task) for task in value]

    def variables(
        self,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        variables = dict(self.vars)

        if overrides:
            variables.update(overrides)

        return variables


class RecipeInvocation(BaseModel):
    name: str
    variables: dict[str, Any] = Field(default_factory=dict)


class RecipeFile(BaseModel):
    recipes: dict[str, Recipe]

    @model_validator(mode="after")
    def set_recipe_names(self) -> RecipeFile:
        for name, recipe in self.recipes.items():
            recipe.name = name

        return self


class RecipeCollection(BaseModel):
    recipes: dict[str, Recipe] = Field(default_factory=dict)

    def merge(self, other: RecipeCollection) -> RecipeCollection:
        recipes = dict(self.recipes)

        for name, recipe in other.recipes.items():
            if name in recipes:
                raise ValueError(f"Duplicate recipe '{name}'")

            recipes[name] = recipe

        return RecipeCollection(recipes=recipes)

    def get(self, name: str) -> Recipe:
        try:
            return self.recipes[name]
        except KeyError:
            raise ValueError(f"Recipe '{name}' does not exist") from None


def load_recipe_file(
    path: str | Path,
) -> dict[str, Recipe]:
    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    recipe_file = RecipeFile.model_validate(data)

    return recipe_file.recipes


def load_recipes(
    paths: list[str | Path],
) -> RecipeCollection:
    recipes: dict[str, Recipe] = {}

    for path in paths:
        for name, recipe in load_recipe_file(path).items():
            if name in recipes:
                raise ValueError(f"Duplicate recipe '{name}' found in '{path}'")

            recipes[name] = recipe

    return RecipeCollection(recipes=recipes)
