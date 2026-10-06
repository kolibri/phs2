from typing import Any

from pydantic import BaseModel, field_validator


class BaseTaskConfig(BaseModel):
    when: str | bool | None = None
    sudo: bool | None = False


class CommandTaskConfig(BaseTaskConfig):
    cmd: str
    pwd: str | None = None


class PackageTaskConfig(BaseTaskConfig):
    name: list[str]

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [value]

        return value


class RepoTaskConfig(BaseTaskConfig):
    url: str
    dest: str


class FileTaskConfig(BaseTaskConfig):
    src: str
    dest: str


class DirTaskConfig(BaseTaskConfig):
    src: str
    dest: str


Task = (
    CommandTaskConfig
    | PackageTaskConfig
    | RepoTaskConfig
    | FileTaskConfig
    | DirTaskConfig
)


def _parse_task(data: Any) -> BaseTaskConfig:
    if not isinstance(data, dict) or len(data) != 1:
        raise ValueError("Each task must contain exactly one task type")

    task_type, task_data = next(iter(data.items()))

    if task_data is None:
        task_data = {}

    if not isinstance(task_data, dict):
        raise TypeError(f"Task '{task_type}' must contain a mapping")

    task_classes = {
        "command": CommandTaskConfig,
        "package": PackageTaskConfig,
        "repo": RepoTaskConfig,
        "file": FileTaskConfig,
        "dir": DirTaskConfig,
    }

    try:
        task_class = task_classes[task_type]
    except KeyError:
        raise ValueError(f"Unknown task type '{task_type}'") from None

    return task_class.model_validate(task_data)
