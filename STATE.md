# State Tracking

| Step | Status | Description |
| ---- | ------ | ----------- |
| H11  | done   | Added 5 MC programs (`p1_sensor`, `p2_actuator`, `p3_uart`, `p4_adc`, `p5_pwm`) resilient respectively to `dropout`/`stuck`, `glitch`, `uart_garbage`, `spike`/`drift`, and `step`/`ramp` faults. Created matching timeline JSONs inside `tests/` leveraging generic expectations across JSON objects tightly mapping the `timeline.schema.json` bounds. Constructed generic Python metric script `judge/score_confidence.py` returning explicitly formatted JSON values independently of PASS/FAIL semantics per instructions. |
