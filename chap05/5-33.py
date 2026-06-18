from machine import UART
import select
uart1 = UART(1, baudrate=115200, tx=23, rx=22)  # 串口1
uart2 = UART(2, baudrate=115200, tx=19, rx=18)  # 串口2

poller = select.poll()
poller.register(uart1,select.POLLIN)            # 注册流对象，监控可读状态
poller.register(uart2,select.POLLIN)

while True:    
    events = poller.poll(1000)                  # 等待事件就绪，超时1000毫秒（1秒） 
    for obj, event, *_ in events:               # 遍历就绪事件,*_吸收多余数据 
        if event & select.POLLIN:               # 检查是否是可读事件（POLLIN）
            data = obj.readline()
            if obj == uart1:   print(f"uart1:{data.decode()}") 
            elif obj == uart2: print(f"uart2:{data.decode()}") 
        elif event & select.POLLERR or event & select.POLLHUP:         # 检查错误和挂起事件
            print(f"{obj}发生错误或流已关闭！") 
            poller.unregister(obj)
