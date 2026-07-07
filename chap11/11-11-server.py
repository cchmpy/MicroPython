import network,socket,tls,myutils
from micropython import const

_HOST = const('0.0.0.0')                                      # 监听所有IP4网络接口
_PORT = const(4433)                                           # DTLS默认端口
network.hostname('esp32-ec')                                  # 设置主机名,可通过hostname.local获取ip

myutils.connect_wifi(timeout=30)                              # 使用正确的ssid和key连接Wi-Fi
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # 创建UDP套接字
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)# 地址重用
udp_sock.bind((_HOST, _PORT))                                 # 绑定端口

ctx = tls.SSLContext(tls.PROTOCOL_DTLS_SERVER)                # 创建服务器模式的SSLContext对象
with open('esp32-ec.der','rb') as fc, open('esp32-ec-key.der','rb') as fk:
    cert = fc.read()                                          # 读取证书
    key = fk.read()                                           # 读取私钥 
ctx.load_cert_chain(cert, key)                                # 加载服务器证书和私钥数据

print('waiting...')
for _ in range(2):                                            # 尝试2次DTLS握手
    _, client_addr = udp_sock.recvfrom(1, socket.MSG_PEEK)    # 等待客户端连接以获取其地址
    udp_sock.connect(client_addr)                             # 重新连接到客户端
    try:
        dtls_sock= ctx.wrap_socket(udp_sock, server_side=True, client_id=repr(client_addr).encode())
    except OSError as err: 
        print(err) 
        continue                                              # 进行第二次连接

for _ in range(5):
    data = dtls_sock.recv(1024)                               # 接收客户端数据
    print(data)
    dtls_sock.send(b'Server received:'+data)                  # 发送数据
dtls_sock.close()                                             # 关闭dtls_sock和upd_sock
