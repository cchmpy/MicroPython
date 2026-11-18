# 示例1，支持多种参数形式创建对象实例，可增强代码可读性，避免复杂__init__()逻辑
class RGBLed: 
    @classmethod
    def from_hex(cls, hex_code):       # 从十六进制字符串创建实例（如 "#FF00FF"） 
        r = int(hex_code[1:3], 16)
        g = int(hex_code[3:5], 16)
        b = int(hex_code[5:7], 16)
        return cls(r, g, b)            # 等同于：RGBLED(r, g, b)
    def __init__(self, r, g, b):
        self._r, self._g, self._b = r, g, b
    def __repr__(self):
        return f'RGBLED({self._r}, {self._g}, {self._b})'
led = RGBLed.from_hex("#FF00FF")       # 使用类方法创建实例
print(led)                             # 输出: RGBLED(255, 0, 255)

# 示例2，根据参数或者硬件状态（如设备的总线接口）等条件动态创建不同类别的实例
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
