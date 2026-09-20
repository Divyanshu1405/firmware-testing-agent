from abc import ABC, abstractmethod
from dataclasses import dataclass
"""Simulator backend redirected to authoritative sim.backend."""

from sim.backend import RenodeBackend
from sim.fake_backend import FakeBackend
from sim.runner import simulate

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
__all__ = ["RenodeBackend", "FakeBackend", "simulate"]
