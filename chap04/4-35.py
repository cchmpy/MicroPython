from machine import Pin,PWM
class Led():
    def __init__(self,pin=23,duty=60):   # duty是百分比亮度
        self._pin,self._duty = pin, duty        
        self._pwm = PWM(Pin(pin),freq=500, duty_u16=int(655.35*self._duty))
    def duty(self,duty=None):            # 获取和设置亮度
        if duty is None: return self._duty
        self._duty = max(0,min(100,duty))
        self._pwm.duty_u16(int(655.35*self._duty))
    def deinit(self):                    # 反初始化方法，释放资源
        self._pwm.deinit()
    def __repr__(self):
        return f'{self.__qualname__}({self._pin},{self._duty})'
    def __str__(self):
        return f'LED[{self._duty}%] on pin {self._pin}'
led = Led(23)
print(repr(led))                         # Led(23,60)
print(led)                               # LED[60%] on pin 23
led.deinit()
