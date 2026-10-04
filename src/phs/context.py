from dataclasses import dataclass

from phs.output import Output
from phs.settings import Settings


@dataclass(frozen=True, slots=True)
class AppContext:
    output: Output
    settings: Settings
