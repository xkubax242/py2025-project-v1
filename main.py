import time
from datetime import datetime
from temperature_sensor import TemperatureSensor
from humidity_sensor import HumiditySensor
from pressure_sensor import PressureSensor
from light_sensor import LightSensor
from logger import Logger

def main():

    logger = Logger('config.json')
    logger.start()


    sensors = [
        TemperatureSensor('temp_01', frequency=1),
        HumiditySensor('hum_01', frequency=1),
        PressureSensor('press_01', frequency=1),
        LightSensor('light_01', frequency=1),
    ]

    try:
        while True:
            now = datetime.now()
            for sensor in sensors:
                if sensor.active:
                    value = sensor.read_value()
                    logger.log_reading(sensor.sensor_id, now, value, sensor.unit)
                    print(f"[{now.isoformat()}] {sensor.name} ({sensor.sensor_id}): {value} {sensor.unit}")
            time.sleep(1)

    except KeyboardInterrupt:
        print("Zatrzymanie loggera...")
    finally:
        logger.stop()

if __name__ == '__main__':
    main()
