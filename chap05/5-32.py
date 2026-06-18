from machine import UART
import select
uart1 = UART(1, baudrate=115200, tx=23, rx=22)  # 串口1
uart2 = UART(2, baudrate=115200, tx=19, rx=18)  # 串口2

while True:    
    readable, _, _ = select.select([uart1,uart2], [], [], 1) # 监控可读状态，超时1秒    
    for x in readable:                          # 处理就绪可读输入流
        if data := x.readline():                # 读取一行
            if x == uart1:  print(f"uart1:{data.decode()}")
            elif x== uart2: print(f"uart2:{data.decode()}")
               
