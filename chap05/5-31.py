from machine import UART
from random import randint
import time
uart1 = UART(1, baudrate=115200, tx=22, rx=23)  # 串口1
uart2 = UART(2, baudrate=115200, tx=18, rx=19)  # 串口2
i,j=0,0
while True:
    i+=1
    j+=1
    uart1.write(f'{i} uart1 message.')          # 串口1发送数据
    time.sleep_ms(randint(500,1000))
    uart2.write(f'{i} uart2 message.')          # 串口2发送数据
    time.sleep_ms(randint(500,1000))