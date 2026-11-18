from machine import UART
import select
uart1 = UART(1, baudrate=115200, tx=23, rx=22,timeout=5,timeout_char=2)  # 串口1
uart2 = UART(2, baudrate=115200, tx=19, rx=18,timeout=5,timeout_char=2)  # 串口2
poller = select.poll()
poller.register(uart1,select.POLLIN)            # 注册流对象，监控可读状态
poller.register(uart2,select.POLLIN)
while True:
    for obj, event, *_ in poller.ipoll(2000):   # 迭代事件就绪的流对象，超时2000毫秒（2秒） 
        if event & select.POLLIN:               # 检查是否是可读事件（POLLIN）
            data = obj.readline()
            if obj is uart1:   print('uart1:', data)
            elif obj is uart2: print('uart2:', data)            
        elif event & select.POLLERR or event & select.POLLHUP: # 检查错误和挂起事件
            print(f"{obj}发生错误或流已关闭！") 
            poller.unregister(obj)