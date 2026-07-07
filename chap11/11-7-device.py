import socket,time,myutils
from machine import Pin
from micropython import const

_BROADCAST_IP = const('255.255.255.255')                       # 广播地址
_GATEWAY_QUERY_PORT = const(30000)                             # 网关监听的端口（必须与网关一致）
_DEVICE_LISTEN_PORT = const(30001)                             # 设备自己监听的端口，用于接收网关回复
_QUERY_MSG = const('WHERE_IS_GATEWAY')                         # 查询网关时发送的信息

smart_led = Pin(23,mode=Pin.OUT,value=0)                       # 假如23引脚连接了led灯,初始关闭

wlan = myutils.connect_wifi()                                  # 使用正确的ssid和key连接Wi-Fi
if not wlan.isconnected(): raise SystemExit                    # 联网失败，则退出解释器
gateway_ip = None                                              # 网关的IP
  
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # 创建UDP socket
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # 设置允许广播
udp_sock.bind(('', _DEVICE_LISTEN_PORT))                       # 绑定设备自己的端口，这样网关才能回复

udp_sock.settimeout(25)                                        # 设置超时时间，避免无限等待
print('开始搜索网关...') 
try:
    udp_sock.sendto(_QUERY_MSG, (_BROADCAST_IP, _GATEWAY_QUERY_PORT)) # 发送广播查询
    data, addr = udp_sock.recvfrom(1024)                       # 等待网关回复
    data = data.decode()
    print(f'收到来自{addr[0]}的回复: {data}')
    
    if data.startswith('GATEWAY_IP:'):                         # 解析回复，提取网关IP
        gateway_ip = data.split(':')[1]
        print(f'发现网关IP地址为: {gateway_ip}') 
except OSError as err:
    print('查找网关过程中出现错误:',err) 
    raise SystemExit
finally: udp_sock.close()

try:                                                            # 与网关通信（示例:发送设备状态）
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    status = 'ON' if smart_led() else 'OFF'
    message = f'STATUS {status} SMART_LED'                      # 状态标志+状态+设备名称
    udp_sock.sendto(message, (gateway_ip, _GATEWAY_QUERY_PORT))
    print(f'已向网关发送状态信息:{message}')
except OSError as err:
    print('与网关通信出错:', err)
finally: udp_sock.close()