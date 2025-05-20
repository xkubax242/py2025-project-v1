import random
import time
from base_sensor import Sensor

class PressureSensor(Sensor):
    def __init__(self, sensor_id, frequency=1):
        super().__init__(
            sensor_id=sensor_id,
            name="Czujnik ciśnienia atmosferycznego",
            unit="hPa",
            min_value=950,
            max_value=1050,
            frequency=frequency
        )

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik '{self.name}' jest nieaktywny.")

        current_hour = time.localtime().tm_hour
        if 6 <= current_hour < 18:
            base_pressure = random.uniform(1000, 1020)
        else:
            base_pressure = random.uniform(980, 1005)

        fluctuation = random.uniform(-5, 5)
        pressure = base_pressure + fluctuation

        pressure = max(self.min_value, min(self.max_value, pressure))
        self.last_value = round(pressure, 2)

        return self.last_value
