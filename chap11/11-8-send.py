import socket,time,gc,myutils
from micropython import const

_MULTICAST_GROUP = const('239.1.2.3')                               # 多播组地址
_MULTICAST_PORT =  const(5000)                                      # 多播端口,与接收端保持一致
_TTL =  const(1)                                                    # TTL=1：仅在本地子网传播
_IP_MULTICAST_TTL =  const(10)                                      # 设置_TTL的选项

# 连接WiFi或创建热点(选择其一）
# myutils.connect_wifi()                                             # 连接Wi-Fi
myutils.create_ap(ssid='ESP32_AP',key='12345678')                    # 创建热点
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)          # 创建UDP套接字（多播基于UDP）
try:
    udp_sock.setsockopt(socket.IPPROTO_IP, _IP_MULTICAST_TTL, _TTL)  # 设置多播TTL（可选步骤）
    print(f'多播TTL已设置为：{_TTL}，仅本地子网传播')
except OSError as err:
    print('设置TTL失败,固件可能不支持：', err)

n = 0
try: 
    while True:                                                       # 向多播组循环发送数据
        msg = f'多播消息[{n}]：Hello Multicast Group!'                  # 待发送多播消息 
        udp_sock.sendto(msg, (_MULTICAST_GROUP, _MULTICAST_PORT))     # 发送到多播组地址和端口
        print(f'已发送：{msg} 到 {_MULTICAST_GROUP}:{_MULTICAST_PORT}')
        n += 1
        gc.collect()                                                  # 垃圾回收
        time.sleep(2)                                                 # 每2秒发送一次
except KeyboardInterrupt: print('已中断发送')
finally: sock.close()                                                 # 关闭套接字
