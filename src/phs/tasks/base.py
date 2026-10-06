from dataclasses import dataclass

from phs.execution import Target
from phs.output import Output


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


class TaskRunner:
    def __init__(self, target: Target):
        self.target = target
    
    def run(self, task: BaseTask, output: Output):
        check_result = task.check(self.target)
        
        if check_result.result:
            output.info(f"Check [ok] {check_result.message}")
            return

        output.info(f"Check [not ok] {check_result.message}")
        execute_result = task.execute(self.target)
        
        if not execute_result.result:
            output.info(f"Execution failed: {execute_result.message}")
            raise TaskExecutionError(execute_result.message)

        output.info(f"Executed: {execute_result.message}")
