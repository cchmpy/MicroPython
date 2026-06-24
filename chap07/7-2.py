from machine import Pin,soft_reset
import time
s1 = Pin(22,Pin.IN,Pin.PULL_UP)         # 开关1：输入模式，内部上拉
s2 = Pin(23,Pin.IN)                     # 开关2：输入模式，外部上拉

while True:   
    if s1()==0 and s2()==0:             # 同时按下两个按键
        while s1()==0 or s2==0: time.sleep_ms(20)            # 延时等待按键被松开（防抖）
        print('Press two buttons')
        break
    elif s1()==0:                       # 按键1被按下
        while s1()==0: time.sleep_ms(20)
        print('Press button1')
    elif s2()==0:                       # 按键2被按下
        while s2()==0: time.sleep_ms(20)
        print('Press button2') 
    time.sleep_ms(50)                   # 检测间隔
