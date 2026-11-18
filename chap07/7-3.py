from micropython import const
from uctypes import INT16, ARRAY, struct, addressof,LITTLE_ENDIAN
from myutils import timeit,gcit
from random import randint
_WIDTH   = const(30)                                     # 图像的像素宽度
_HEIGHT  = const(30)                                     # 图像的像素高度
class ThermalProcessor :                                 # 热成像数据处理类
    @staticmethod
    def rgb565(r,g,b):                           # 将三基色转换成小端序的RGB565
        return (b>>3 | (g&0x1C)<<3)<<8 | (r&0xF8 | g>>5) 
    
    def __init__(self): 
        self._buf = bytearray(_WIDTH*_HEIGHT*2)  # 一帧像素（温度数据）的缓存
        # 定义一帧像素对应的二维数组_data2、一维数组_data1
        self._data2 = struct(addressof(self._buf),
                             (ARRAY, _HEIGHT,(ARRAY, _WIDTH | INT16)),LITTLE_ENDIAN)
        self._data1 = struct(addressof(self._buf),
                             (ARRAY, _HEIGHT * _WIDTH | INT16),LITTLE_ENDIAN) 
    @timeit('ms')
    @gcit
    def convert1(self):                           # 使用一维数组处理数据   
        data = self._data1                        # 用局部变量缓存实例变量，加快访问速度
        for i in range(_HEIGHT*_WIDTH):
            data[i] = randint(-4000,30000)        # 用随机数模拟热成像的像素值
            v = data[i]//100                      # data[i]像素点的实际温度
            b = 0; g = 0; r = 0
            if v<0:      b = 255*(0-v)//40        # 低温：蓝色通道幅度值
            elif v<=100: g = 255*v//100           # 中温：绿色通道幅度值
            else:        r = 255*(v-100)//200     # 高温：红色通道幅度值
            data[i] = self.rgb565(r,g,b)          # 转换为小端序RGB565颜色值
    @timeit('ms')
    @gcit
    def convert2(self):                           # 使用二维数组处理数据  
        data = self._data2 
        for i in range(_HEIGHT):
            for j in range(_WIDTH):
                data[i][j] = randint(-4000,30000) 
                v = data[i][j]/100                # data[i][j]像素点的实际温度
                if v<0:      b,g,r = int(255*(0-v)/40), 0, 0  # 低温：蓝
                elif v<=100: b,g,r = 0,int(255*v/100), 0      # 中温：绿           
                else:        b,g,r = 0,0,int(255*(v-100)/200) # 高温：红
                data[i][j] = self.rgb565(r,g,b) 
if __name__ == '__main__':
    tp = ThermalProcessor()
    print('convert1：'); tp.convert1() 
    print('convert2：'); tp.convert2() 