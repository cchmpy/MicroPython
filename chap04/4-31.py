from machine import Pin,PWM
class Servo:
    _pin_servos = {}                          # key是引脚, value是引脚对应的Servo对象
    _first_init = True  
    def __new__(cls, pin, *args, **kwargs): 
        if pin not in cls._pin_servos.keys(): # 如果该引脚上没有创建过舵机对象
            cls._first_init = True
            cls._pin_servos[pin] = object.__new__(cls)
        return cls._pin_servos[pin]
    def __init__(self, pin):
        if self._first_init:
            self._first_init = False 
            self.pwm = PWM(Pin(pin), duty=0, freq=50)
servo1 = Servo(23)
servo2 = Servo(23)
print(servo1 is servo2)                     # True, 复用同一对象
