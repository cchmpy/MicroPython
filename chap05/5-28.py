import time
from machine import Timer
import micropython as mpy
class TestRingIO:
    def __init__(self):        
        self.s = (b'1aaaa',b'2bbbb',b'3cccc',b'4dddd',b'5eeee',b'6ffff')      # 循环写入的数据
        self.i = 0                                                            # self.s的下标
        self.rio = mpy.RingIO(11)                                             # 定义RingIO对象实例
        self.t = Timer(0,mode = Timer.PERIODIC,period=200,callback=self._cb)  # 定时器
    def _cb(self,_): 
        self.rio.write(self.s[self.i])                                        # 写入RingIO
        self.i=(self.i+1)% len(self.s)                                        # 更新下标（数据）
    def read_print(self,n=-1):
        if self.rio.any():  print(self.rio.read(n))                           # 读取并打印
    def deinit(self):
        self.t.deinit()

r = TestRingIO() 
while True:
    try:
        r.read_print(5)                                         # 可设置读取字节数
        time.sleep_ms(400)                                      # 可以调整读取速度,以观察结果
    except KeyboardInterrupt:
        r.deinit()
        break
