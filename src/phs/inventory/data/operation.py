from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PackageOperation(BaseModel):
    type: Literal["package"]
    packages: list[str]


class RepoOperation(BaseModel):
    type: Literal["repo"]
    url: str
    dest: str


class FileOperation(BaseModel):
    type: Literal["file"]
    src: str
    dest: str
    owner: str | None = None
    group: str | None = None
    sudo: bool = False


class DirOperation(BaseModel):
    type: Literal["dir"]
    src: str
    dest: str
    owner: str | None = None
    group: str | None = None
    sudo: bool = False


class RecipeOperation(BaseModel):
    type: Literal["recipe"]
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


Operation = (
    PackageOperation | RepoOperation | FileOperation | DirOperation | RecipeOperation
)
