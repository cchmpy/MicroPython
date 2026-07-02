from micropython import const
from myutils import timeit
_CNT = const(100)
@timeit('ms')                              
def rgb565_byte():           #  字节码发射器
    x = 0
    for r in range(_CNT):
        for g in range(_CNT):
            for b in range(_CNT): x = (b>>3 | (g&0x1C)<<3)<<8 | (r&0xF8 | g>>5)            
@timeit('ms')
@micropython.native 
def rgb565_native():        #  本地码发射器
    x = 0
    for r in range(_CNT):
        for g in range(_CNT):
            for b in range(_CNT): x = (b>>3 | (g&0x1C)<<3)<<8 | (r&0xF8 | g>>5)
                     
@timeit('ms')
@micropython.viper
def rgb565_viper():         #  viper码发射器
    x = 0
    for r in range(_CNT):
        for g in range(_CNT):
            for b in range(_CNT): x = (b>>3 | (g&0x1C)<<3)<<8 | (r&0xF8 | g>>5)

rgb565_byte()               # 运行时间: 13311ms
rgb565_native()             # 运行时间: 6736ms
rgb565_viper()              # 运行时间: 409ms

