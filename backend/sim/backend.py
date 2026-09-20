from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SimulationResult:
    simulator: str
    success: bool
    stdout: str = ""
    stderr: str = ""


class SimBackend(ABC):
    name: str

    @abstractmethod
    def run(self, timeline: dict) -> SimulationResult:
        raise NotImplementedError
