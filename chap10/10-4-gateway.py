import socket, time, myutils
from micropython import const

_GATEWAY_IP = const('0.0.0.0')                               # 监听所有网络接口
_LISTEN_PORT = const(30000)                                  # 网关监听的广播端口

wlan = myutils.connect_wifi()                                # 使用正确的ssid和key连接Wi-Fi
if not wlan.isconnected(): raise SystemExit                  # 联网失败，则退出解释器
gateway_ip = wlan.ifconfig()[0]                              # 网关的IP

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 创建 UDP socket
udp_sock.bind((_GATEWAY_IP, _LISTEN_PORT))                   # 绑定到指定端口，监听所有网络接口
print(f'网关已启动，正在端口{_LISTEN_PORT}监听设备查询...') 
while True:
    try:
        data, addr = udp_sock.recvfrom(1024)                 # 接收来自设备的数据包
        if data:
            data = data.decode().strip()
            print(f'收到{addr}的信息:{data}')
            if data == 'WHERE_IS_GATEWAY':                   # 判断是查找网关的请求
                udp_sock.sendto(f'GATEWAY_IP:{gateway_ip}', addr)  # 向查询设备回复IP
                print(f'已把网关IP告知了设备{addr[0]}')
            elif data.startswith('STATUS'):                  # 判断是设备发送的状态信息
                if 'ON' in data: print(f'已开灯')
                elif 'OFF' in data: print(f'已关灯')
    except OSError as err:
        print('网关服务出错:', err)
        udp_sock.close()
        break