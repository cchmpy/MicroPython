import socket, select, sys
class PollTCPServer:                               # 通用多路复用TCP Socket服务器
    def __init__(self): 
        self.poller = select.poll()                # poll类对象
        self.svr_sock = None                       # 服务器socket 
        self.sock_queue = {}    # 发送队列：socket为键，发送队列列表为值
        self.on_connect = None  # 用户接口，参数(PollTCPServer, clt_sock, addr)
        self.on_recv = None     # 用户接口，参数(PollTCPServer, clt_sock, data)
        
    def _clear_sock(self,sock):         # 清理指定的套接字（注销、关闭、删字典）
        try: self.poller.unregister(sock)          # 从poll对象中注销
        except: pass
        try: sock.close()                          # 关闭套接字
        except: pass
        if sock in self.sock_queue: del self.sock_queue[sock]  # 从字典中删除
    
    def _clear_all(self):                          # 清理服务器和所有客户端套接字
        for clt_sock in list(self.sock_queue):     # 清空客户端套接字
            self._clear_sock(clt_sock)
        self._clear_sock(self.svr_sock)            # 清理服务器套接字
        
    def send(self, sock, data):                    # 对外接口：发送数据 
        if sock in self.sock_queue: 
            self.sock_queue[sock].append(data)     # 向发送队列添加数据 
            self.poller.modify(sock, select.POLLIN | select.POLLOUT) # 修改检测事件
            return True
        return False

    def run(self, host='0.0.0.0', port=8080, poll_timeout=50):   # 服务器启动入口
    # 参数host可为IPv4地址或域名，poll_timeout超时毫秒数
        self.svr_sock = socket.socket()            # TCP套接字
        self.svr_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # 地址复用
        self.svr_sock.bind(('0.0.0.0', port))      # 绑定通用接口
        self.svr_sock.listen(5)
        self.svr_sock.setblocking(False)           # poll轮询时必须设为非阻塞
        self.poller.register(self.svr_sock, select.POLLIN)  # 注册服务器套接字
        print(f'== {host}:{port} 已启动==')        # 打印服务器IPv4或域名
        print('[Ctrl+C退出]')

        while True:
            try:
                for sock, event, *_ in self.poller.ipoll(poll_timeout):  # poll轮询
                    if sock is self.svr_sock:      # 服务器收到连接请求
                        clt_sock, addr = self.svr_sock.accept()  # 接受客户端连接
                        clt_sock.setblocking(False) 
                        self.poller.register(clt_sock, select.POLLIN) # 注册客户端
                        self.sock_queue[clt_sock] = []   # 初始化发送队列（空列表）
                        print(f'{addr}客户端连接.')
                        if self.on_connect:              # 调用回调on_connect()
                            self.on_connect(self, clt_sock, addr) 
                    elif event & select.POLLIN:          # 客户端有可读数据
                        data = sock.read()               # 读取全部
                        if not data:                     # 清理客户端,继续遍历
                            print('客户端主动关闭')
                            self._clear_sock(sock); continue
                        if self.on_recv:                 # 有数据，调用on_recv回调
                            self.on_recv(self, sock, data)
                    elif event & select.POLLOUT:         # sock写缓冲区空闲，可写入
                        queue = self.sock_queue[sock]
                        if not queue:      # 无要写入数据：取消POLLOUT,避免CPU空转
                            self.poller.modify(sock, select.POLLIN); continue 
                        data=queue[0]; size=sock.write(data)# 发送数据
                        if size == len(data): queue.pop(0)  # 已发送完
                        else: queue[0] = data[size:]        # 未发送完 
                    elif event & (select.POLLERR | select.POLLHUP): 
                        print('客户端异常(ERR/HUP)') 
                        self._clear_sock(sock)              # 清理异常的客户端socket
            except KeyboardInterrupt:
                print('== 退出服务器 ==')
                self._clear_all(); break                    # 清理所有套接字,退出主循环
            except OSError as e:
                sys.print_exception(e)
                if sock is self.svr_sock:                   # 若是服务器异常
                    print('服务器异常，断开所有连接.')
                    self._clear_all(); break                # 清理所有套接字,退出主循环 
                else:                                       # 若是客户端异常
                    print('客户端异常或断开连接')
                    self._clear_sock(sock); continue        # 清理异常的客户端,继续主循环 
if __name__ == '__main__':                                  # 回声服务器示例
    from myutils import connect_wifi
    from network import hostname
    hostname('esp32-poll')                                  # 服务器主机名
    wlan = connect_wifi()    
    def on_recv(server,clt_sock, data):                     # 定义回调函数
        print("收到:", data.strip().decode())
        server.send(clt_sock, data)
    server = PollTCPServer()
    server.on_recv = on_recv
    server.run(host=f'{hostname()}.local', port=8080)