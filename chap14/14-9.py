from machine import Pin, PWM
class Servo:
    def __init__(self, pin):
        self._pwm   = PWM(Pin(pin), duty=0, freq=50)
        self._factor = None              # 计算duty的因数：angle/180或者(speed+100)/200

    def _write(self,factor):
        self._factor=factor
        self._pwm.duty_u16(int(6553.5*self._factor+1638.375))
        
    def servo180_angle(self,angle=None):
        if angle is None: return int(self._factor*180)
        if 0<=angle<=180: self._write(angle/180)
        else:  raise ValueError('The angle must be 0~180')
    
    def servo360_speed(self,speed=None):
        if speed is None:  return int(self._factor*200-100)
        if -100<=speed<=100: self._write((speed+100)/200) 
        else:   raise ValueError('The speed must be -100~100')
        
    def deinit(self):
        self._pwm.deinit()

if __name__ == '__main__':
    import time
    def foo(s,i):
        s.servo180_angle(i)
        time.sleep_ms(3)
    s = Servo(13)    
    for i in range(181):       foo(s,i)  # 从0转到180
    for i in range(180,-1,-1): foo(s,i)  # 从180转到0
    s.deinit()
