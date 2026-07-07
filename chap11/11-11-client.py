import socket,tls,myutils
from micropython import const

_HOST = const('esp32-ec.local')                               # 待访问服务器的主机名/域名
_PORT = const(4433)                                           # DTLS对应默认端口号
myutils.connect_wifi(timeout=30)                              # 使用正确的ssid和key连接Wi-Fi
myutils.sync_ntp()                                            # 同步日期时间,验证证书时需要正确的日期

sock_addr = socket.getaddrinfo(_HOST,_PORT)[0][-1]            # 获取服务器端的套接字地址
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # 创建UPD套接字
udp_socket.connect(sock_addr)                                 # 此处是DTLS层的“虚拟连接”，不是TCP连接

ctx = tls.SSLContext(tls.PROTOCOL_DTLS_CLIENT)                # 创建客户端模式的SSLContext
with open('rootCA.der','rb') as f: cadata = f.read()          # 读取根证书数据
ctx.load_verify_locations(cadata)                             # 载入证书链数据，以验证服务器身份
ctx.verify_mode = tls.CERT_REQUIRED                           # 验证模式:需要验证
try:
    dtls_sock = ctx.wrap_socket(udp_socket, server_hostname=_HOST) # 包装套接字
except OSError as err:
    print(err)
    raise SystemExit                                          # 抛出异常退出程序
for i in range(5):    
    dtls_sock.send(f"client to server {i}")                   # 发送数据
    print(dtls_sock.recv(1024))                               # 接收数据
dtls_sock.close()                                             # 关闭dtls_sock和udp_sock