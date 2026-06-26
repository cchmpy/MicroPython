from machine import I2C,Pin
import vl53l0x,time                                               # 引用程序14-3.py（vl53l0x）
xshut1, xshut2 = Pin(19,Pin.OUT,value=1), Pin(18,Pin.OUT,value=0) # 上电时，关闭第二个传感器
i2c= I2C(0,scl = Pin(22),sda = Pin(23))                           # 公共I2C总线 
vl_1 = vl53l0x.VL53L0X(i2c,address=0x35,timeout_ms=1000,gpio1=21) # 设置地址0x35
xshut2(1)                                                         # 使能传感器2
vl_2 = vl53l0x.VL53L0X(i2c,address=0x36,timeout_ms=1000)          # 设置地址0x36
try:
    while True:
        vl_1.range_single()     # 单次测量模式
        vl_2.range_single()
        print('range1:',vl_1.read_in_poll(),'range2:',vl_2.read_in_poll(),'\n') 
        time.sleep(1)
except KeyboardInterrupt: xshut1(0);  xshut2(0)                   # 关闭模块
