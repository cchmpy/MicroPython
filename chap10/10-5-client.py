import socket,ssl,myutils
from micropython import const
_HOST = const('esp32-ec.local')         # 要访问的域名
_PORT = const(443)                      # HTTPS默认端口号
myutils.connect_wifi()                  # 使用正确的ssid和key连接Wi-Fi
myutils.sync_ntp()                      # 同步日期,验证证书时需要正确的日期
sock_addr = socket.getaddrinfo(_HOST,_PORT)[0][-1]  # 获取套接字地址

with open('rootCA.der', 'rb') as f: CA_CERT = f.read() # 读取根证书
sock = socket.socket()                  # 创建TCP套接字，之后连接、包装
sock.connect(sock_addr)
ssl_sock = ssl.wrap_socket(sock,
    server_side   = False,              # 客户端模式
    cert_reqs     = ssl.CERT_REQUIRED,  # 必须验证服务器证书（防中间人攻击）
    cadata        = CA_CERT,            # 用根证书验证
    server_hostname = _HOST)            # 指定服务器主机名（SNI + 证书域名校验）
# 发送HTTP请求 / 接收响应
ssl_sock.write(f'GET / HTTP/1.1\r\nHost: {_HOST}\r\nConnection: close\r\n\r\n')
print(ssl_sock.read(1024))
ssl_sock.close()
