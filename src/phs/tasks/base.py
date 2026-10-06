from dataclasses import dataclass

from phs.execution import Target


class TaskExecutionError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class CheckResult:
    result: bool
    message: str


@dataclass(frozen=True, slots=True)
class ExecuteResult:
    result: bool
    message: str


class BaseTask:
    def check(self, target: Target) -> CheckResult:
        pass

    def execute(self, target: Target) -> ExecuteResult:
        pass
