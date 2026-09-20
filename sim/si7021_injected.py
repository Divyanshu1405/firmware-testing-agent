"""SI7021 I2C model with full fault-injection semantics for Renode tests."""

_sensor_instance = None


class SI7021Injected:
    def __init__(self, peripheral):
        global _sensor_instance
        self.peripheral = peripheral
        self.temperature_c = 25.0
        self.humidity_pct = 50.0
        self.is_dropped = False
        self.force_error = False
        self.stuck_temp = None
        self.stuck_humidity = None
        self.include_crc = False

        peripheral.DataReceived += self.on_write
        _sensor_instance = self

    def on_write(self, data):
        if not data:
            return

        # If sensor is dropped / disconnected, do not enqueue any response (causes I2C NACK / timeout)
        if self.is_dropped:
            return

        command = data[0]

        # Read RH (Relative Humidity): command 0xF5 (no hold master) or 0xE5 (hold master)
        if command in (0xF5, 0xE5):
            if self.force_error:
                self.peripheral.EnqueueResponseBytes(bytes([0xFF, 0xFF]))
                return

            val = self.stuck_humidity if self.stuck_humidity is not None else self.humidity_pct
            self.peripheral.EnqueueResponseBytes(self._measurement(val, 6.0, 125.0, self.include_crc))

        # Read Temperature: 0xE3 (hold), 0xF3 (no hold), 0xE0 (read temp from previous RH measurement)
        elif command in (0xE3, 0xE0, 0xF3):
            if self.force_error:
                self.peripheral.EnqueueResponseBytes(bytes([0xFF, 0xFF]))
                return

            val = self.stuck_temp if self.stuck_temp is not None else self.temperature_c
            self.peripheral.EnqueueResponseBytes(self._measurement(val, 46.85, 175.72, self.include_crc))

        # Soft reset
        elif command == 0xFE:
            self.is_dropped = False
            self.force_error = False

    @classmethod
    def _measurement(cls, value, offset, scale, include_crc=False):
        raw = int(max(0, min(0xFFFC, round((value + offset) * 65536.0 / scale))))
        msb = (raw >> 8) & 0xFF
        lsb = raw & 0xFC
        if include_crc:
            crc = cls._crc8([msb, lsb])
            return bytes([msb, lsb, crc])
        return bytes([msb, lsb])

    @staticmethod
    def _crc8(data):
        crc = 0
        for byte in data:
            if not isinstance(byte, int):
                byte = ord(byte)
            crc ^= byte
            for _ in range(8):
                crc = ((crc << 1) ^ 0x31) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
        return crc


def mc_setup_si7021(path):
    global _sensor_instance
    _sensor_instance = SI7021Injected(path)


def mc_set_temperature(val):
    global _sensor_instance
    if _sensor_instance:
        _sensor_instance.temperature_c = float(val)


def mc_set_humidity(val):
    global _sensor_instance
    if _sensor_instance:
        _sensor_instance.humidity_pct = float(val)


def mc_set_sensor_dropout(val):
    global _sensor_instance
    if _sensor_instance:
        _sensor_instance.is_dropped = bool(int(val))


def mc_set_sensor_error(val):
    global _sensor_instance
    if _sensor_instance:
        _sensor_instance.force_error = bool(int(val))


def mc_set_sensor_stuck(channel, val):
    global _sensor_instance
    if _sensor_instance:
        ch = str(channel).lower()
        if "temp" in ch:
            _sensor_instance.stuck_temp = float(val)
        elif "humid" in ch:
            _sensor_instance.stuck_humidity = float(val)


def mc_clear_sensor_stuck():
    global _sensor_instance
    if _sensor_instance:
        _sensor_instance.stuck_temp = None
        _sensor_instance.stuck_humidity = None


def mc_set_crc_enabled(val):
    global _sensor_instance
    if _sensor_instance:
        _sensor_instance.include_crc = bool(int(val))
