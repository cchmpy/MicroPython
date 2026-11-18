class I2CDevice:
    _i2c = None                                     # 类级共享变量
    @classmethod
    def init_i2c(cls, id, scl_pin, sda_pin):
        from machine import I2C,Pin
        cls._i2c = I2C(id, scl=Pin(scl_pin), sda=Pin(sda_pin))
    def __init__(self, address):
        if self._i2c is None:
            raise RuntimeError("I2C bus not initialized!")
        self._addr = address
I2CDevice.init_i2c(id=0, scl_pin=18, sda_pin=19)   # 初始化I2C总线，只调用一次
dev1 = I2CDevice(address=0x20)                     # 创建设备实例
dev2 = I2CDevice(address=0x21)                     # 创建设备实例
