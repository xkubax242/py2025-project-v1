from base_sensor import Sensor
import math
import time
import random

class TemperatureSensor(Sensor):
    def __init__(self, sensor_id, frequency=1):
        super().__init__(
            sensor_id=sensor_id,
            name="Symulowany Czujnik Temperatury",
            unit="°C",
            min_value=-20.0,
            max_value=50.0,
            frequency=frequency
        )

    def read_value(self):
        if not self.active:
            raise RuntimeError(f"{self.name} ({self.sensor_id}) jest nieaktywny.")

        current_hour = time.localtime().tm_hour
        base_daily_cycle = math.sin((2 * math.pi * current_hour) / 24)
        base_temp = 20 + (8 * base_daily_cycle) 

        fluctuation = random.uniform(-1.5, 1.5)
        simulated_value = base_temp + fluctuation

        self.last_value = round(
            max(self.min_value, min(self.max_value, simulated_value)), 2
        )
        return self.last_value
