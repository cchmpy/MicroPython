from machine import I2C,Pin
import vl53l0x,time                      # 引用程序14-3.py（vl53l0x）
xshut = Pin(19,Pin.OUT,value=1)          # 模块开关引脚
i2c= I2C(0,scl = Pin(22),sda = Pin(23)) 
vl = vl53l0x.VL53L0X(i2c,timeout_ms=1000)
vl.range_continuous(500)                 # 连续定时模式 500ms测距一次 
try:
    while True:
        print(vl.read_in_poll())
        time.sleep_ms(500)
except KeyboardInterrupt: xshut(0)       # 关闭模块