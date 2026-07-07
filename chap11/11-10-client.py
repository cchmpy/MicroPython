import socket,ssl,select,myutils
from micropython import const
from errno import EINPROGRESS
_HOST = const('esp32-ec.local')                     # 待访问服务器的主机名/域名
_PORT = const(443)                                  # HTTPS对应默认端口号

def connect_nonblocking(sock, addr):                # 非阻塞连接函数
    sock.setblocking(False)
    try:
        sock.connect(addr)
    except OSError as err:
        if err.errno != EINPROGRESS: raise err      # 忽略EINPROGRESS异常(操作正在进行中)
        
def write_nonblocking(poller, sock, data):          # 非阻塞发送函数
    poller.register(sock, select.POLLOUT)
    while data:
        poller.poll()                               # 轮询等待是否能写入更多数据
        n = sock.write(data)
        print("Wrote:", n)
        if n is not None: data = data[n:]

def read_nonblocking(poller, sock, n):              # 非阻塞读取函数
    poller.register(sock, select.POLLIN)
    poller.poll()                                   # 轮询等待是否有可读取数据
    data = sock.read(n)
    print("Read:", len(data))
    return data

myutils.connect_wifi(timeout=30)                    # 使用正确的ssid和key连接Wi-Fi
myutils.sync_ntp()                                  # 同步日期时间,验证证书时需要正确的日期
# 1. 准备数据
sock_addr = socket.getaddrinfo(_HOST,_PORT)[0][-1]  # 获取套接字地址
with open('rootCA.der','rb') as f:                  # 读取根证书数据集
    CA_CERT = f.read()
# 2. 创建TCP套接字、连接、包装
client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connect_nonblocking(client_sock, sock_addr)         # 非阻塞连接***************
ssl_sock = ssl.wrap_socket(client_sock,server_side=False,
    cert_reqs=ssl.CERT_REQUIRED,                    # 必须验证服务器证书
    cadata=CA_CERT,                                 # 传入根证书数据
    server_hostname=_HOST,                          # 服务器证书的主机名
    do_handshake=False)                             # 推迟TLS握手**************
ssl_sock.setblocking(False)                         # 设置非阻塞模式************
# 3. 读写等操作
poller = select.poll()                              # 创建poll对象用于轮询ssl_sock
request =f'GET / HTTP/1.1\r\nHOST: {_HOST}\r\nConnection: close\r\n\r\n' # HTTP请求
write_nonblocking(poller, ssl_sock, request)        # 发送请求*****************
print(read_nonblocking(poller, ssl_sock, 1024))     # 接收并打印数据************
ssl_sock.close()                                    # 关闭连接
