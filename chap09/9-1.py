import _thread,time
from machine import Pin
def blink(led:Pin,period_ms):
    while True:
        led.toggle()
        time.sleep_ms(period_ms)
red = Pin(23,mode=Pin.OUT)
green = Pin(22,mode=Pin.OUT)

_thread.start_new_thread(blink,(red,500))                   # 启动线程1
_thread.start_new_thread(blink,(green,),{'period_ms':800})  # 启动线程2

n = 0
while True:                  # 主线程的循环
    if (n := n+1)>9999: n=0
    print(f'{n:4}\r',end='') 
    time.sleep(1)
 