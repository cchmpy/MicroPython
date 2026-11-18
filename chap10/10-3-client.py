import socket, myutils, time
from random import randint
wlan = myutils.connect_wifi()                                 # 使用正确的ssid和key连接Wi-Fi
ip = wlan.ifconfig()[0]                                       # 本机IP地址
svr_addr = socket.getaddrinfo('esp32-poll.local',8080)[0][-1] # 获取服务器端的套接字地址
client_sock = socket.socket()                                 # 创建TCP套接字
try:   
    client_sock.connect(svr_addr); i=0                        # 连接服务器（阻塞等待）
    while True:                                               # 开始对话
        client_sock.write(f'{ip} message {i}\n')              # 发送数据
        print('服务器:',client_sock.readline().strip().decode()) # 打印服务器回复
        time.sleep(randint(1,5)); i += 1                      # 等待1～5秒        
except OSError as err: print(err)                             # 打印错误信息
except KeyboardInterrupt: print('关闭客户端')
finally: client_sock.close()                                  # 关闭套接字
