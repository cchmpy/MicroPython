import network,socket,ssl,time,myutils
from micropython import const

_HOST = const('0.0.0.0')                                           # 监听所有网络接口
_PORT = const(443)                                                 # HTTPS默认端口
network.hostname('esp32-ec')      # 设置主机名,客户端可通过https://hostname.local访问
myutils.connect_wifi(timeout=30)                                   # 用正确的ssid和key连接Wi-Fi

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    # 创建TCP套接字
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 地址重用
server_sock.bind((_HOST, _PORT))                                   # 绑定端口
server_sock.listen(2)                                              # 开始监听
print(f'HTTPS服务器{network.hostname()}.local正在{_HOST}:{_PORT}监听...')

while True:
    client_sock, addr = server_sock.accept()                       # 等待接受客户端连接
    try:
        # 将accept()返回的客户端套接字包装成SSLSocket 
        ssl_client_sock = ssl.wrap_socket(client_sock, server_side=True,
            key='esp32-ec-key.der',                                # 服务器端私钥文件
            cert='esp32-ec.der')                                   # 服务器端证书文件 
        
        print('客户端请求:\n',ssl_client_sock.recv(4096))          # 接收客户端请求,为简化未解析请求信息
        response = '''HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\nHello, Secure World!'''
        ssl_client_sock.write(response)                            # 发送HTTP响应 
        ssl_client_sock.close()                                    # 关闭TLS连接
    except OSError as err:
        print(f'处理时出错: {err}')
        client_sock.close()
    time.sleep(1)