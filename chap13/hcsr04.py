from machine import Pin, time_pulse_us
from time import sleep_us
from micropython import const
# 目标为500CM时超声波常温下的传播时间（传播1cm需29.1us≈30us）
_TIMEOUT_US = const(30000)                         # 500*2*30=30ms
class HCSR04:
    def __init__(self,trig,echo,timeout_us=_TIMEOUT_US,centigrade=20): 
        self._c = 331.5+0.607*centigrade           # 当前温度对应的声速m/s
        self._timeout_us = timeout_us
        self._trig = Pin(trig,Pin.OUT,value=0)
        self._echo = Pin(echo,Pin.IN) 

    def range_cm(self):                            # 测距并返回以cm为单位的结果
        self._trig(0); self._trig(1)
        sleep_us(10)                               # 维持高电平至少10us
        self._trig(0)                              # 下降沿触发测量
        pulse_us = time_pulse_us(self._echo, 1, self._timeout_us) 
        if pulse_us<0:  pulse_us=self._timeout_us  # 若返回-1 or -2,测量超时
        return round(pulse_us*self._c/20000,2)
if __name__=='__main__':
    import time
    h = HCSR04(trig=23,echo=22)
    while True:
        print(h.range_cm()); time.sleep(1)
