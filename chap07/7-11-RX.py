from machine import UART
import time
buf = bytearray(7)
head = b'\xAA\x55\x03' # 帧头+长度
uart1 = UART(1,baudrate=115200,rx=13, tx=12)
while True:    
    if uart1.any():
        size = uart1.readinto(buf)
        if size!=7 or not buf.startswith(head): continue  # 长度或帧头不对，忽略此次数据       
        check_sum = (sum(buf)-buf[-1]) & 0xff       
        if buf[-1] != check_sum:  continue                # 校验和不对
        print(f'{buf[3]} {buf[4]} {buf[5]}   \r', end='') # 打印温度、湿度、火焰检测结果
    time.sleep(2)
