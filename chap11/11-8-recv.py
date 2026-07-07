import socket,gc,myutils
from micropython import const

_MULTICAST_GROUP = const('239.1.2.3')                          # 多播组地址
_MULTICAST_PORT = const(5000)                                  # 多播组端口
connect_wifi(ssid='ESP32_AP',key='12345678')                   # 连接Wi-Fi或ESP32热点

# 模拟socket.inet_pton，将文本IP地址转换为网络字节序的二进制字节流。支持IPv4（AF_INET）
# 例如'192.168.1.1' → b'\xc0\xa8\x01\x01'
def inet_pton(af, txt_addr):
    if af == socket.AF_INET:
        parts = txt_addr.split('.')                            # 处理IPv4：点分十进制（如'192.168.1.1'）
        if len(parts) != 4:                                    # 校验格式：必须是4个部分
            raise ValueError('Invalid IPv4 address (must have 4 parts)')
        result = bytearray(4)
        for i in range(len(parts)): 
            if not parts[i].isdigit():                         # 校验每个部分是否为数字且在0-255范围内
                raise ValueError(f'Invalid IPv4 part: {parts[i]} (not a number)')
            num = int(parts[i])
            if num < 0 or num > 255:
                raise ValueError(f'IPv4 part {num} out of range (0-255)')
            result[i]=num 
        return result
    else:                                                      # 不支持 af = socket.AF_INET6 或其它值
        raise ValueError(f'Unsupported address family {af}')

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # 创建UDP套接字
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # 允许端口复用（可选）
udp_sock.bind(('0.0.0.0', _MULTICAST_PORT))                    # 绑定到多播端口以接收数据

try:                                                           # 加入多播组
    udp_sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP, 
        inet_pton(socket.AF_INET,_MULTICAST_GROUP)+
        inet_pton(socket.AF_INET,'0.0.0.0'))
    print(f'已加入多播组{_MULTICAST_GROUP}')
except OSError as err:
    print('加入多播组失败：', err)                             # 若固件不支持，会抛出错误

try:                                                           # 使用recvfrom()循环接收多播数据
    while True:
        data, addr = udp_sock.recvfrom(1024)
        print(f'收到来自 {addr} 的多播数据：{data.decode()}')
        gc.collect()
except KeyboardInterrupt: pass
finally: udp_sock.close()
