from .backend import SimBackend, SimulationResult


class RenodeBackend(SimBackend):
    name = "renode"

    def run(self, timeline: dict) -> SimulationResult:
        raise NotImplementedError("Implement Renode CLI/socket execution here.")
