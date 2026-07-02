from micropython import const
from uctypes import INT16, ARRAY, struct, addressof,LITTLE_ENDIAN
from myutils import timeit,gcit
from random import randint
_WIDTH   = const(30)                                          # 图像像素宽 cols
_HEIGHT  = const(30)                                          # 图像像素高 rows
class Foo:
    @staticmethod
    def rgb565(r,g,b):
        return (b>>3 | (g&0x1C)<<3)<<8 | (r&0xF8 | g>>5)      # 将三基色转换成小端序的RGB565
    
    def __init__(self): 
        self._buf = bytearray(_WIDTH*_HEIGHT*2)               # 一帧温度数据的缓存
        # 定义二维数组
        self._data2 = struct(addressof(self._buf),(ARRAY, _HEIGHT, (ARRAY, _WIDTH | INT16)),LITTLE_ENDIAN)
        # 定义一维数组
        self._data1 = struct(addressof(self._buf),(ARRAY, _HEIGHT * _WIDTH | INT16),LITTLE_ENDIAN)
    
    @gcit
    #@timeit('ms')
    def convert2(self):
        data = self._data2                                    # 用局部变量缓存类变量，加快访问速度
        for i in range(_HEIGHT):
            for j in range(_WIDTH):
                data[i][j] = randint(-4000,30000)             # v模拟data[i][j]像素点的真实数据
                v = data[i][j]/100
                if v<0:      b,g,r = int(255*(0-v)/40), 0, 0  # 低温：蓝
                elif v<=100: b,g,r = 0,int(255*v/100), 0      # 中温：绿           
                else:        b,g,r = 0,0,int(255*(v-100)/200) # 高温：红
                data[i][j] = Foo.rgb565(r,g,b)                # 2字节温度值原地转换为rgb565颜色值
    @gcit
    #@timeit('ms')
    def convert1(self):
        data = self._data1
        for i in range(_HEIGHT*_WIDTH):
            data[i] = randint(-4000,30000) 
            v = data[i]//100
            b = 0
            g = 0
            r = 0
            if v<0:      b = 255*(0-v)//40                    # 低温：蓝
            elif v<=100: g = 255*v//100                       # 中温：绿 
            else:        r = 255*(v-100)//200                 # 高温：红 
            data[i] = Foo.rgb565(r,g,b)     

foo = Foo()
foo.convert2()  
foo.convert1()  
