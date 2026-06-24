from machine import Pin
import time
cnt = 0                        # 全局变量，按键被触发次数（下降沿数量）
def handle(pin):               # 中断回调函数，必须有一个参数，表示一个Pin对象
    global cnt
    cnt += 1                   # 累加
    print(cnt,'\r',end='')     # 单行打印触发次数
    
s = Pin(34, Pin.IN)            # 使用了按键模块，自带上拉电阻
s.irq(handle,Pin.IRQ_FALLING)  # 定义引脚对象的中断回调函数和触发方式
try:
    while True: time.sleep(1)  # 休眠等待按键被触发
except KeyboardInterrupt: pass # ctrl+c中断程序
s.irq(None)                    # 禁用中断