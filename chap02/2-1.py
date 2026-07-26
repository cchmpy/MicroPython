import neopixel,time
from machine import Pin
from random import randint
class Blink:
    def __init__(self,pin, ws2812=True, period_ms=500):  
        # 参数ws2812：True使用WS2812灯珠，False使用LED灯
        self._pin = Pin(pin,Pin.OUT) 
        self._np = neopixel.NeoPixel(self._pin,1) if ws2812 else None 
        self._period_ms= period_ms         # 闪灯周期（毫秒）       
    def deinit(self):                      # 关灯
        if self._np is None: self._pin(0) 
        else: self._np[0]=0,0,0; self._np.write()       
    def blink(self):                       # 闪灯方法
        try:
            while True:
                if self._np is None:       # LED灯
                    self._pin.toggle()     # 电平交替变换
                else:                      # 以随机颜色点亮WS2812灯珠
                    self._np[0]= randint(0,200),randint(0,200),randint(0,200) 
                    self._np.write()       # 写入RGB值
                time.sleep_ms(self._period_ms)
        except KeyboardInterrupt: pass     # 捕获Ctrl+C键盘中断
        self.deinit() 
if __name__ == '__main__':
    WS2812 = True                          # 修改全局变量，设置灯珠类型，False为LED灯
    b = Blink(16, WS2812, 1000)            # 根据实际情况修改引脚
    b.blink()                              # 按Ctrl+C退出