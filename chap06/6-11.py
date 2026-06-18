from micropython import const
from machine import mem32
import  time
_GPIO_OUT_REG    = const(0x3FF44004)  # GPIO 0-31 输出寄存器地址
_GPIO_ENABLE_REG = const(0x3FF44020)  # GPIO 0-31 输出使能寄存器地址
_M23 = const(1 << 23)                 # Pin(23)引脚的位掩码
mem32[_GPIO_ENABLE_REG] |= _M23       # 使能引脚输出模式，等同Pin(23, mode=Pin.OUT)
raw = mem32[_GPIO_OUT_REG]            # 输出寄存器原始值
try:
    while True:
        mem32[_GPIO_OUT_REG] ^= _M23  # 交替输出高低电平，控制led灯的亮灭
        time.sleep(1)                 # 延时1秒
except KeyboardInterrupt: pass
finally:    
    mem32[_GPIO_OUT_REG] = raw        # 恢复原始值