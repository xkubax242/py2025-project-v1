import random
import time
import math
from base_sensor import Sensor

class LightSensor(Sensor):
    def __init__(self, sensor_id, frequency=1):
        sensor_name = "Czujnik światła"
        sensor_unit = "lx"
        min_value = 0
        max_value = 10000
        super().__init__(sensor_id, sensor_name, sensor_unit, min_value, max_value, frequency)

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        current_hour = time.localtime().tm_hour

        if 6 <= current_hour <= 18:
            base_light = 10000 * math.sin(math.pi * (current_hour - 6) / 12)
        else:
            base_light = random.uniform(0, 20)

        noise = random.uniform(-100, 100)
        light_level = base_light + noise
        light_level = max(self.min_value, min(self.max_value, light_level))

        self.last_value = round(light_level, 2)
        return self.last_value
