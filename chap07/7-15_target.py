# I2C从设备 ESP32-S3
from machine import I2CTarget,Pin,PWM
import time

led = PWM(4,freq=500,duty=0,invert=True)   # 控制低电平触发的LED模块
led.duty(0)
addr,buf = 0x66, bytearray(8)              # I2C从设备地址,后台内存/寄存器,buf[0]控制亮度
r,w = 0, 0                                 # IRQ_END_READ和IRQ_END_WRITE事件触发的次数
i2c = I2CTarget(1,addr,mem=buf,scl=8,sda=9)

def irq_handler(i2c_target):               # 中断回调函数
    global buf,led,r,w
    flags = i2c_target.irq().flags()       # 事件标志
    if flags & I2CTarget.IRQ_END_READ:     # 主设备读取完成
        r+=1 
    if flags & I2CTarget.IRQ_END_WRITE:    # 主设备写入完成
        w+=1
        led.duty(buf[0]*1023//255)         # 根据主设备的写入数据调节LED的亮度            
i2c.irq(irq_handler)
print('The target device has been started...')
       
try:
    while True:
        print(f'IRQ_END_READ:{r} IRQ_END_WRITE:{w}  \r',end='') # 单行打印两个事件被触发的次数
        time.sleep(1)
except KeyboardInterrupt:
    led.duty(0)
    i2c.deinit()
    led.deinit()
