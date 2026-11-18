from machine import UART
from random import randint
from time import ticks_ms, ticks_diff, ticks_add, sleep_ms
import select
uart1 = UART(1, baudrate=115200, tx=22, rx=23)  # 串口1
uart2 = UART(2, baudrate=115200, tx=18, rx=19)  # 串口2
poller = select.poll()                          # 创建poll轮询对象
poller.register(uart1, select.POLLOUT)          # 监听串口1POLLOUT（可写）事件
poller.register(uart2, select.POLLOUT)
i, j = 0, 0                                     # 消息发送计数器
next_send_u1, next_send_u2 = 0, 0               # 两个串口下次发送时间戳（单位ms）
while True:
    now = ticks_ms()                            # 当前时间戳
    for obj, event, *_ in poller.ipoll(2000):   # 迭代事件就绪的流对象 
        if event & select.POLLOUT:              # 检查是否是可写事件
            if obj is uart1 and ticks_diff(now, next_send_u1) >= 0:
                i += 1
                uart1.write(f'uart1 message {i}.\n')           # 发送消息，带换行符
                # 设置下次发送时间：当前时间+随机500~2000ms
                next_send_u1 = ticks_add(now, randint(500, 2000)) 
            elif obj is uart2 and ticks_diff(now, next_send_u2) >= 0:
                j += 1
                uart2.write(f'uart2 message {j}.\n')
                next_send_u2 = ticks_add(now, randint(500, 2000)) 
        elif event & select.POLLERR or event & select.POLLHUP: # 检查错误和挂起事件
            print(f"{obj}发生错误或流已关闭！") 
            poller.unregister(obj)
    sleep_ms(10)
