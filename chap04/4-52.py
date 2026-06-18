from machine import I2C, Pin
class I2CManager:
    def __init__(self, scl_pin, sda_pin):
        self.i2c = I2C(scl=Pin(scl_pin), sda=Pin(sda_pin))    
    def __enter__(self):
        print("I2C总线初始化")
        return self    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("释放I2C资源")
        if exc_type is not None:
            print(f"发生异常: {exc_type.__name__}: {exc_val}") 
        return True                           # 返回True表示已处理异常，不再向上传播 

with I2CManager(25, 26) as i2c_scan:          # I2C总线初始化
    devices = i2c_scan.i2c.scan()
    print("发现的I2C设备:", devices)         # 发现的I2C设备: []
    raise TypeError('模拟抛出异常')           # 释放I2C资源 - 发生异常: TypeError: 模拟抛出异常
