import socket,struct,time,errno,myutils
from machine import deepsleep
from micropython import const
_SSID = const('ESP32_AP')       # AP热点名称
_KEY  = const('12345678')       # AP热点密码
_HOST = const('0.0.0.0')        # 本地IP地址(使用通用地址)
_PORT = const(23456)            # 本地端口号

_INTERVAL_MS = const(1*60*1000) # 交换信息的时间间隔(毫秒,实际应用可设为5分钟)
_TIMEOUT_S   = const(0.5*60)    # socket超时秒数(秒,实际应用可设为2分钟)
_BACKLOG = const(3)             # 客户端最大挂起总数(据实设定)
_LOG_FILE = const('sd/log.txt') # 记录数据的日志文件
clients = 0                     # 已连接的客户端

ap = myutils.create_ap(_SSID,_KEY)                            # 创建热点
svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建TCP套接字
svr_sock.settimeout(_TIMEOUT_S)                               # 设置socket操作超时时间（秒数）
svr_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)# 重用套接字地址
svr_sock.bind((_HOST, _PORT))                                 # 绑定套接字地址
svr_sock.listen(_BACKLOG)                                     # 开始监听

start = time.ticks_ms()  # 同步时间元点,相对该点的_INTERVAL_MS后,再次唤醒系统(包括客户端)
while True:                                                   # 循环接受客户端连接
    try:
        client_sock, client_addr = svr_sock.accept()          # 接受客户端连接（阻塞等待）
        clients += 1                                          # 已连接的客户端数量
        data = client_sock.recv(5)                            # 接收客户端数据（5字节，据实设定）
        if data:
            data = struct.unpack("<BI",data)                  # 将数据解压为元组
        else: data ='No Data'                                 # 客户端关闭了连接
        
        myutils.log(f'{client_addr} {data}',_LOG_FILE,'INFO') # 记录数据到日志文件 
        ms = max(0,_INTERVAL_MS-time.ticks_diff(time.ticks_ms(),start)) # 当前客户端的睡眠时间（毫秒）
        client_sock.write(ms.to_bytes(4))                     # 回复客户端,发送睡眠时间
        # client_sock.close()                                 # 注意，不要关闭client_sock
        if clients>=_TOTAL_CLIENTS: break                     # 已完成所有客户端的处理,退出循环
    except OSError as err:        
        myutils.log(err,_LOG_FILE)                            # 将错误记录到日志文件 
        if err.errno == errno.ETIMEDOUT: break                # 如果超时,则退出循环

time.sleep(1)                                                 # 等待最后连接的客户端接收数据
svr_sock.close()                                              # 关闭服务器套接字
temp = time.ticks_diff(time.ticks_ms(),start)                 # 服务器处理时间
print(f'客户端:{clients},用时{temp},进入睡眠...')             # 打印提示信息
myutils.log(f'用时{temp}ms\n',_LOG_FILE,'INFO')               # 记录该时间，用于分析能耗
deepsleep(max(0,_INTERVAL_MS-temp-2000))                      # 比客户端提前2秒唤醒
