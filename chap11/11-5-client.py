import socket,time,struct,sys,myutils
from micropython import const
from machine import deepsleep
from random import randint
_SSID = const('ESP32_AP')       # AP热点名称
_KEY  = const('12345678')       # AP热点密码
_HOST = const('192.168.4.1')    # 目标服务器IP地址
_PORT = const(23456)            # 目标服务器端口号
_INTERVAL_MS = const(1*60*1000) # 交换信息的时间间隔(毫秒,实际应用可设为5分钟)
_TIMEOUT_S   = const(0.5*60)    # socket超时秒数(秒,实际应用可设为2分钟)
_LOG_FILE = const('log.txt')    # 记录数据的日志文件

def get_sensor_data():          # 模拟读取传感器数据
    return struct.pack('<BI',randint(0,255),randint(0,65535))

def get_sleep_ms(start):        # 获取睡眠时间
    temp = time.ticks_diff(time.ticks_ms(),start)
    return max(0,_INTERVAL_MS - temp)

start = time.ticks_ms()                         # 时间元点
try:
    sta = myutils.connect_wifi(_SSID,_KEY,10)   # 连接WiFi   
except Exception:
    sta = None
if not sta or not sta.isconnected():            # 连接失败
    print('连接热点失败，直接睡眠...')
    deepsleep(get_sleep_ms(start))              # 直接休眠,等待下次连接
    
client_sock = socket.socket()                   # 创建TCP套接字
client_sock.settimeout(_TIMEOUT_S)              # 设置超时秒数
try:   
    client_sock.connect((_HOST, _PORT))         # 连接服务器（阻塞等待）
    data = get_sensor_data()                    # 读取传感器数据
    client_sock.write(data)                     # 发送数据     
    ms = client_sock.recv(4)                    # 等待服务器回复(睡眠毫秒数)
    if ms:
        ms = int.from_bytes(ms)                 # 收到回复
        print('收到回复:',ms)
    else:
        ms = get_sleep_ms(start)                # 未收到服务器回复
    print(f'睡眠{ms}毫秒...')
    client_sock.close()                         # 关闭套接字   
    deepsleep(ms)       
except OSError as err:
    sys.print_exception(err)                    # 打印错误信息
    myutils.log(err,_LOG_FILE)                  # 日志记录错误信息
    deepsleep(get_sleep_ms(start))

    

