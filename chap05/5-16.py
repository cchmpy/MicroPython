import network, socket, myutils, time
from random import randint
def html(temp, hum):                                  # 客户端请求时发送的反馈内容（响应头和html网页）
    return f'''HTTP/1.1 200 OK
Content-Type: text/html
Connection: close\r\n\r\n
<html><head>
    <meta charset="UTF-8">
    <link rel="icon" href="data:,">
</head><body>
    <h1>环境服务</h1>
    <p>温度: {temp}°C</p>
    <p>湿度: {hum}%</p>
</body></html>
'''
def build_listen():    
    network.hostname('esp32-es')                        # 设置主机名,可通过http://esp32-es.local访问
    wlan = myutils.connect_wifi('name','psw')           # 连接wifi,使用正确的用户名和密码代替    
    server_socket = socket.socket()                     # 定义套接字对象
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # 允许重启后立即重用相同的端口
    server_socket.bind(('0.0.0.0',80))                  # 绑定到本机所有可用的网络接口地址，80端口
    server_socket.listen(5)                             # 启动监听
    print(f'http://{network.hostname()}.local/已启动...')
    while True:
        try:
            conn, addr = server_socket.accept()         # 接收客户端连接 
            conn.settimeout(1.0)                        # 设置接收数据超时
            request = conn.recv(1024)                   # 接收客户端请求消息 
            if b'GET / ' in request:                    # 客户端发出http://esp32-es.local/请求
                conn.send(html(randint(20,40),randint(0,100)))                 # 发送HTTP响应
        except KeyboardInterrupt:
            server_socket.close()                       # 关闭服务器套接字
            break
        except Exception as err: 
            print(err)
            time.sleep(1)
        finally: 
            try: conn.close()                          # 关闭客户端连接
            except: pass 
build_listen()
