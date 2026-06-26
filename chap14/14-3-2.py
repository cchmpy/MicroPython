from machine import I2C,Pin,PWM
import vl53l0x,time                            # 引用程序14-3.py（vl53l0x）
xshut = Pin(19,Pin.OUT,value=1)
i2c= I2C(0,scl = Pin(22),sda = Pin(23)) 
vl = vl53l0x.VL53L0X(i2c,timeout_ms=1000,gpio1=21)
led2 = PWM(Pin(2),freq=1,duty=512)             # Pin2引脚的led灯
def cb(_):
    global vl,led2
    data=min(vl.read_in_callback(),1200)
    led2.init(freq=(7-data//200))              # 设置led灯闪烁频率，距离越近频率越高 

vl.interrupt_config(vl.INT_DATA_RDY,handle=cb) # 设置中断模式
vl.range_continuous()                          # 开启连续测量模式
try:
    while True: time.sleep_ms(500)
except KeyboardInterrupt:  xshut(0)            # 关闭模块