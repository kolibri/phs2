from phs.execution.target import Target
from phs.inventory.config import DiskConfig
from phs.tasks.base import BaseTask, CheckResult, ExecuteResult


class Disk(BaseTask):
    data: DiskConfig

    def check(self, target: Target) -> CheckResult:
        pass

    def execute(self, target: Target) -> ExecuteResult:
        pass


