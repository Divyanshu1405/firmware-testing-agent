"""Compatibility stub for Wokwi, which is not a supported runtime backend."""

from .backend import SimBackend, SimulationResult


class WokwiBackend(SimBackend):
    """Fail explicitly until a Wokwi adapter is implemented."""

    name = "wokwi"

    def run(self, timeline: dict) -> SimulationResult:
        del timeline
        raise NotImplementedError(
            "Wokwi simulator backend is not configured. Use the Renode backend."
        )
