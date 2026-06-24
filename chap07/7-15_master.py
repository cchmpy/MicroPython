# I2C主设备 ESP32
from machine import I2C
import time
i2c = I2C(0,scl=23, sda=22)
addr = 0x66
print(i2c.scan())                     # 打印对从设备的扫描结果
buf,direction = bytearray(1), 1       # 写入led模块缓冲、占空比变化的方向
try:
    while True:
        if buf[0]==255: direction=-1
        elif buf[0]<=15: direction=1
        buf[0] += 15*direction        # buf[0]保存占空比数值
        i2c.writeto_mem(addr,0,buf)   # 向从设备led模块写入占空比
        time.sleep_ms(200)
except (KeyboardInterrupt,Exception):
    i2c.writeto_mem(addr,0,b'\x00')   # 退出前尝试关闭led

    
            