from uctypes import BFUINT16, BFUINT32,BF_POS, BF_LEN, struct, addressof
import time
data = bytearray(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08')
addr = addressof(data)
desc = {'bitx': 0 | BFUINT16 | 4<<BF_POS | 4<<BF_LEN,  # 位域在圆括号位置：0b0000 0000 (0000) 0000
        'bity': 2 | BFUINT16 | 8<<BF_POS | 4<<BF_LEN}  # 位域在圆括号位置：0b0000 (0000) 0000 0000 
s = struct(addr,desc)
s.bitx = 0b1111    
s.bity = 0b1111
print(s.bitx, s.bity)         # 输出：15 15
print(data[:4])               # 输出：bytearray(b'\xf0\x01\x02\x0f')

# 通过操作寄存器位域值控制引脚GPIO23高低电平输出
GPIO_OUT_REG    = 0x3FF44004  # GPIO 0-31 输出寄存器地址,对应使能寄存器0x3FF44020
gpio23_desc = {'value': 0 | BFUINT32 | 23<<BF_POS | 1<<BF_LEN,
               'en':   28 | BFUINT32 | 23<<BF_POS | 1<<BF_LEN,}
gpio23 = struct(GPIO_OUT_REG,gpio23_desc)
gpio23.en = 0b1               # 23引脚输出使能
try:    
    while True:
        gpio23.value ^= 0b1   # 交替变换高低电平
        time.sleep(1)
except KeyboardInterrupt: pass
finally:
    gpio23.value = 0          # 设为低电平
    gpio23.en    = 0          # 禁止输出
