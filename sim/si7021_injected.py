"""Minimal SI7021 I2C model for deterministic Renode tests."""

_sensor_instance = None


class SI7021Injected:
    def __init__(self, peripheral):
        global _sensor_instance
        self.peripheral = peripheral
        self.temperature_c = 25.0
        self.humidity_pct = 51.0
        peripheral.DataReceived += self.on_write
        _sensor_instance = self

    def on_write(self, data):
        if not data:
            return
        command = data[0]
        if command == 0xF5:
            self.peripheral.EnqueueResponseBytes(self._measurement(self.humidity_pct, 6.0, 125.0))
        elif command in (0xE3, 0xE0, 0xF3):
            self.peripheral.EnqueueResponseBytes(
                self._measurement(self.temperature_c, 46.85, 175.72)
            )

    @staticmethod
    def _measurement(value, offset, scale):
        raw = int(max(0, min(0xFFFC, round((value + offset) * 65536 / scale))))
        payload = bytes([(raw >> 8) & 0xFF, raw & 0xFC])
        return payload

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
