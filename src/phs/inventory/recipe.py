from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class TaskBase(BaseModel):
    when: str | bool | None = None


class PackageTask(TaskBase):
    name: list[str]

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [value]

        return value


class RepoTask(TaskBase):
    url: str
    dest: str


class FileTask(TaskBase):
    src: str
    dest: str


class DirTask(TaskBase):
    src: str
    dest: str


class Task(BaseModel):
    package: PackageTask | None = None
    repo: RepoTask | None = None
    file: FileTask | None = None
    dir: DirTask | None = None

    @model_validator(mode="after")
    def exactly_one_task(self) -> "Task":
        values = [
            self.package,
            self.repo,
            self.file,
            self.dir,
        ]

        if sum(value is not None for value in values) != 1:
            raise ValueError(
                "A task must contain exactly one of: package, repo, file, dir"
            )

        return self


class Recipe(BaseModel):
    name: str | None = None
    vars: dict[str, Any] = Field(default_factory=dict)
    tasks: list[Task] = Field(default_factory=list)

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


def load_recipe_file(path: str | Path) -> dict[str, Recipe]:
    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    recipe_file = RecipeFile.model_validate(data)

    return {
        name: recipe.model_copy(update={"name": name})
        for name, recipe in recipe_file.recipes.items()
    }


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
