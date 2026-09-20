from .backend import SimBackend, SimulationResult


class WokwiBackend(SimBackend):
    name = "wokwi"

    def run(self, timeline: dict) -> SimulationResult:
        raise NotImplementedError("Implement Wokwi CLI execution here.")
