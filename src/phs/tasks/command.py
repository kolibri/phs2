from dataclasses import dataclass

from phs.execution import Target
from phs.inventory.tasks import CommandTaskConfig
from phs.tasks.base import BaseTask, CheckResult, ExecuteResult


@dataclass(frozen=True)
class CommandTask(BaseTask):
    data: CommandTaskConfig

    def check(self, target: Target) -> CheckResult:
        return CheckResult(False, "Commands dont check")

    def execute(self, target: Target) -> ExecuteResult:
        result = target.run(self.data.cmd)

        if result.returncode != 0:
            return ExecuteResult(False, result.stderr)

        return ExecuteResult(True, result.stdout)
