import neopixel,time
from machine import Pin
from random import randint
class Blink:
    def __init__(self,pin, is_rgb=True, period_ms=500):        # is_rgb为True表示是RGB灯，否则是led灯
        self._pin = Pin(pin,Pin.OUT)        
        self._np = neopixel.NeoPixel(self._pin,1) if is_rgb else None  # 定义NeoPixel对象,控制1个RGB灯
        self._period_ms= period_ms 
        
    def deinit(self):                      # 关灯
        if self._np is None:
            self._pin(0)                   # 关闭led
        else:
            self._np[0]=0,0,0              # 关闭rgb
            self._np.write()
    
    def blink(self):
        try:
            while True:
                if self._np is None:       # 普通led灯
                    self._pin.toggle()     # 交替电平变换
                else:                      # 以随机颜色点亮rgb灯
                    self._np[0]= randint(0,200),randint(0,200),randint(0,200)  # 设置第一个灯的rgb值
                    self._np.write()       # 写入rgb值
                time.sleep_ms(self._period_ms)
        except KeyboardInterrupt: pass     # 捕获ctrl+c键盘中断
        self.deinit() 
            
if __name__=='__main__':
#     bk = Blink(23, False, 1000)          # led灯
    bk = Blink(16, True, 1000)             # rgb灯
    bk.blink()
