from phs.execution import Target
from phs.inventory.facts import Facts


class FactCollector:
    def __init__(self, target: Target):
        self.target = target

    def collect(self) -> Facts:
        pass
