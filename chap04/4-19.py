class SensorError(Exception):
    def __init__(self, code, message):
        self.code = code                       # 自定义属性
        self.message = message
def read_sensor():
    raise SensorError(500, "传感器读取失败")
try:
    read_sensor()
except SensorError as err:
    print(f"错误码 {err.code}: {err.message}")  # 输出: 错误码 500: 传感器读取失败
