import random
import time
from sensors.base_sensor import Sensor

class HumiditySensor(Sensor):
    def __init__(self, sensor_id, frequency=1):

        super().__init__(
            sensor_id=sensor_id,
            name="Czujnik wilgotności",
            unit="%",
            min_value=0,
            max_value=100,
            frequency=frequency
        )

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik '{self.name}' jest wyłączony.")

        current_hour = time.localtime().tm_hour

        if 5 <= current_hour < 9 or 18 <= current_hour < 22:
            base_humidity = random.uniform(65, 85)
        elif 9 <= current_hour < 18:
            base_humidity = random.uniform(35, 55)
        else:
            base_humidity = random.uniform(55, 75)

        noise = random.uniform(-4, 4)
        raw_value = base_humidity + noise
        final_value = max(self.min_value, min(self.max_value, raw_value))
        self.last_value = round(final_value, 2)
        return self.last_value
