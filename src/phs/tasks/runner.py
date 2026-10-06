from enum import Enum

from phs.execution import Target
from phs.output import Output
from phs.tasks.base import BaseTask, TaskExecutionError


class RunMode(Enum):
    CONFIRM = "confirm"
    NO_CONFIRM = "no_confirm"
    DRY_RUN = "dry_run"


class TaskRunner:
    def __init__(
        self,
        target: Target,
        output: Output,
        mode: RunMode = RunMode.CONFIRM,
    ):
        self.target = target
        self.output = output
        self.mode = mode

    def run(self, task: BaseTask):
        check_result = task.check(self.target)

        if check_result.result:
            self.output.info(f"Check [ok] {check_result.message}")
            return

        self.output.info(f"Check [not ok] {check_result.message}")

        if self.mode == RunMode.DRY_RUN:
            self.output.info("Dry run mode: task not executed")
            return

        if self.mode == RunMode.CONFIRM:
            answer = self.output.prompt("Confirm? [Y/n] ").strip().lower() or "y"
            if answer != "y":
                self.output.info("Canceled: task not executed.")
                return

        execute_result = task.execute(self.target)

        if not execute_result.result:
            self.output.info(f"Execution failed: {execute_result.message}")
            raise TaskExecutionError(execute_result.message)

        self.output.info(f"Executed: {execute_result.message}")
