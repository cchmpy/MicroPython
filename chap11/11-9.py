import socket,ssl,myutils
from micropython import const
_HOST = const('micropython.org')                    # 待访问的主机名/域名
_PORT = const(443)                                  # HTTPS对应默认端口号
myutils.connect_wifi()                              # 使用正确的ssid和key连接Wi-Fi
myutils.sync_ntp()                                  # 同步日期时间,验证证书时需要正确的日期
# 1. 准备数据
sock_addr = socket.getaddrinfo(_HOST,_PORT)[0][-1]  # 获取套接字地址
with open('ISRG Root X1.der','rb') as f:            # 读取根证书
    CA_CERT = f.read()
# 2. 创建TCP套接字、连接、包装
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(sock_addr)
ssl_sock = ssl.wrap_socket(sock,server_side=False,
    cert_reqs=ssl.CERT_REQUIRED,                    # 必须验证服务器证书
    cadata=CA_CERT,                                 # 传入根证书数据
    server_hostname=_HOST)                          # 服务器证书的主机名
# 3. 读写等操作
ssl_sock.write(f'GET / HTTP/1.1\r\nHOST: {_HOST}\r\nConnection: close\r\n\r\n') # 发送HTTP请求
print(ssl_sock.recv(1024))                          # 打印接收的数据
ssl_sock.close()                                    # 关闭连接