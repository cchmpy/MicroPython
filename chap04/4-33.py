from machine import Pin,PWM
class Led():
    def __init__(self,pin=23,duty=60):    # duty是百分比亮度
        self._pin,self._duty = pin, duty        
        self._pwm = PWM(Pin(pin),freq=500, duty_u16=int(655.35*self._duty))
    def duty(self,duty=None):             # 获取和设置亮度
        if duty is None: return self._duty
        self._duty = max(0,min(100,duty))
        self._pwm.duty_u16(int(655.35*self._duty))
    def deinit(self):                     # 反初始化方法，释放资源
        self._pwm.deinit()
led = Led(22)                             # 定义对象，自动调用__init__()完成初始化
led.duty(80)                              # 设定亮度
led.deinit()                              # 释放资源
