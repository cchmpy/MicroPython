from machine import ADC, Pin
class Sensor:                       # 父类（抽象模板）
    def read_data(self):            # 模板方法(定义逻辑框架)
        self.setup()                # 步骤1：初始化（由子类实现）
        raw = self._read()          # 步骤2：读取数据（由子类实现）
        return self.process(raw)    # 步骤3：处理数据（可由子类覆盖）

    def setup(self):                # 抽象方法（子类必须实现）
        raise NotImplementedError("Subclass must implement setup()")

    def _read(self):                # 抽象方法（子类必须实现）
        raise NotImplementedError("Subclass must implement _read()")

    def process(self, data):        # 钩子方法（子类可选覆盖）
        return data * 0.1           # 默认处理逻辑

class TemperatureSensor(Sensor):    # 子类
    def setup(self):                # 实现父类的同名抽象方法        
        self.adc = ADC(Pin(26))     # 硬件初始化

    def _read(self):                # 实现父类的同名抽象方法
        return self.adc.read_u16()  # 实际读取硬件

sensor = TemperatureSensor()
print(sensor.read_data())           # 父类调用子类的 setup() 和 _read()
