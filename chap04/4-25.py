class Sensor:
    def __init__(self, pin):
        self.pin = pin
    @classmethod
    def create(cls, sensor_type, pin):
        if sensor_type == "DHT11":     return DHT11(pin)      # 返回子类实例
        elif sensor_type == "DS18B20": return DS18B20(pin)
        raise ValueError("Unknown sensor type")

class DHT11(Sensor):
    def read(self):  return {"temp": 25.0, "humidity": 50}    # 返回字典类型
class DS18B20(Sensor):
    def read(self): return {"temp": 26.5}

sensor = Sensor.create("DHT11", pin=22)
print(sensor.read())                                          # 输出: {'humidity': 50, 'temp': 25.0}
