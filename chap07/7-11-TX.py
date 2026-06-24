from machine import UART,Signal,Pin
import time,dht
uart1 = UART(1,baudrate=115200,rx=12, tx=13)
fire = Signal(18,Pin.IN,invert=False)      # 火焰传感器
dht11 = dht.DHT11(19)                      # 温湿度传感器
# UART发送一帧数据的格式：AA 55 03(数据长度) 温度 湿度 火焰 校验和
buf = bytearray(b'\xAA\x55\x03\x00\x00\x00\x00')
while True:
    dht11.measure()                        # 测量
    buf[3] = dht11.temperature()           # 读取温度（摄氏度）
    buf[4] = dht11.humidity()              # 读取湿度
    buf[5] = fire()                        # 火焰探测结果
    buf[6] = (sum(buf)-buf[-1]) & 0xFF     # 计算校验和    
    print(f'{buf.hex(' ')} \r', end='')    # 单行打印发送数据
    uart1.write(buf)     
    time.sleep(2)                          # 每2秒测量并发送一次数据