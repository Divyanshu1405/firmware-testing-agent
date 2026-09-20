TEST FIXTURE ONLY — not the real firmware spec, do not use for the actual scoreboard/demo.

# Sample Firmware Specification

This document outlines the operational limits and expected behavior of the cooling module.

1. The main cooling fan MUST activate within 1000 ms when the core temperature exceeds 30.0°C.
2. If the temperature stays above 45.0°C for >= 5000 ms, the system MUST initiate an emergency shutdown.
3. The fan speed should feel appropriate for the noise level of the environment.
4. When the temperature drops below 25.0°C, the fan MUST deactivate within 500 ms to conserve power.
5. The system SHALL log a warning if the secondary sensor reading differs from the primary by more than 5.0°C for > 2000 ms.
