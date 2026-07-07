import socket,network,time
from myutils import connect_wifi
sta = connect_wifi()                              # 连接Wi-Fi，注意使用正确的ssid和key
client = socket.socket()                          # 创建TCP套接字
server_addr = socket.getaddrinfo('www.micropython.org',80)[0][-1]       # 解析服务器地址
client.connect(server_addr)                       # 连接服务器
# 发送HTTP请求,使用请求头字段"Connection: close",确保操作完成后关闭连接
client.send('GET / HTTP/1.1\r\nHost: www.micropython.org\r\nConnection: close\r\n\r\n')
try:
    while True:
        data = client.read(1024)                  # 循环读取1024个字节，直到EOF
        if data:
            print(data.decode())
        else:                                     # 服务器关闭，收到EOF，data=b''
            print("服务器已关闭连接")
            break
except OSError as err:
    print("读取失败：", err)
finally:
    client.close()                                # 关闭套接字
