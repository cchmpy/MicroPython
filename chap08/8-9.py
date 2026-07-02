import micropython,time
from machine import Pin,Timer
micropython.alloc_emergency_exception_buf(100)
class LED:
    def __init__(self, timer, led_pin,freq):
        self.cnt = 0                           # 闪灯次数
        self.led = Pin(led_pin,mode=Pin.OUT,value=0)
        timer.init(mode=Timer.PERIODIC,freq=freq,callback=self.cb)
    def cb(self, _):                           # 定时器中断回调程序
        self.led.toggle()                      # 电平切换
        self.cnt = (self.cnt+1) % 1_000_001    # 最大计数100万，然后再从0开始
        
timer0,timer1 = Timer(0),Timer(1)
red, green = LED(timer0, 23, 1), LED(timer1, 22, 0.5)

try:
    while True:
        print(f'red:{red.cnt}      green:{green.cnt}      \r', end='')
        time.sleep(1)
except KeyboardInterrupt:
    timer0.deinit()
    timer1.deinit()
