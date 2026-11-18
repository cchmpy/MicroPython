from micropython import const
from myutils import timeit
_CNT = const(100)
@timeit('ms') 
def rgb565_byte():           #  默认使用字节码发射器
    x = 0
    for r in range(_CNT):
        for g in range(_CNT):
            for b in range(_CNT): x = (b>>3 | (g&0x1C)<<3)<<8 | (r&0xF8 | g>5) 
@timeit('ms')
@micropython.native        #  本地码发射器
def rgb565_native():
    x = 0
    for r in range(_CNT):
        for g in range(_CNT):
            for b in range(_CNT): x = (b>>3 | (g&0x1C)<<3)<<8 | (r&0xF8 | g>>5)
@timeit('ms')
@micropython.viper        #  viper码发射器
def rgb565_viper():
    x = 0
    for r in range(_CNT):
        for g in range(_CNT):
            for b in range(_CNT): x = (b>>3 | (g&0x1C)<<3)<<8 | (r&0xF8 | g>>5)
rgb565_byte()               # 运行时间: 13311ms
rgb565_native()             # 运行时间: 6736ms，比使用字节码发射器快约2倍
rgb565_viper()              # 运行时间: 409ms，比使用字节码发射器快约32倍
