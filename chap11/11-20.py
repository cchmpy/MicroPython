import sys
_path=sys.path; sys.path=()                                # 备份/清空sys.path
try: from websocket import websocket                       # 载入固件内置websocket.websocket
finally: sys.path=_path; del _path                         # 恢复sys.path默认值,删除_path

from os import urandom
from binascii import b2a_base64, a2b_base64
from hashlib import sha1
import socket, ssl, select
from micropython import const

# 协议规定的固定GUID
WS_GUID = const('258EAFA5-E914-47DA-95CA-C5AB0DC85B11') 
# ioctl(request, arg), request参数值:关闭流\获取帧格式\设置帧格式
STREAM_CLOSE=const(4); GET_FRAME_TYPE=const(8); SET_FRAME_TYPE=const(9)
# ioctl(request, arg), arg参数值:文本帧\二进制帧\关闭帧\心跳Ping\心跳Pong
FRAME_TXT=const(1);  FRAME_BIN=const(2); FRAME_CLOSE=const(8); FRAME_PING=const(9); FRAME_PONG=const(10)

# -------扩展函数1: client_key(), 生成客户端Sec-WebSocket-Key----------------------------------------
client_key = lambda : b2a_base64(urandom(16),newline=False).decode() 
# -------扩展函数2: server_key(clt_key),生成服务器端 Sec-WebSocket-Accept ---------------------------
def server_key(clt_key): 
    c = clt_key + WS_GUID                                   # 拼接客户端Key+固定GUID 
    h = sha1(c.encode()).digest()                           # SHA-1 哈希（bytes对象）
    return b2a_base64(h,newline=False).decode()             # 生成Base64编码(str对象)
#--------扩展函数3: client_key_valid(clt_key),服务器验证Sec-WebSocket-Key是否有效-------------------
def client_key_valid(clt_key:str): 
    if (len(clt_key) != 24) or (not clt_key.endswith('==')):# 校验长度和结尾
        return False 
    try:                                                    # 验证是否为BASE64编码（尝试解码并重新编码）
        return b2a_base64(a2b_base64(clt_key),newline=False).decode()==clt_key
    except Exception: return False
#--------扩展函数4: server_key_valid(clt_key,svr_key),客户端验证Sec-WebSocket-Accept是否有效---------
def server_key_valid(clt_key:str, svr_key): 
    return server_key(clt_key)==svr_key

#--------扩展通用服务器类: WSServer, I/O多路复用（并发）服务器----------------------------------------
class WSServer:                                             # WebSocket 服务器类
    def __init__(self, max_ws_clients=5):       
        self.html=None; self.html_file=None                 # 静态主页（html文本/html文件，优先使用文本）
        self.max_clients_cnt = max_ws_clients               # 最大WebSocket客户端数量
        self.cur_clients_cnt = 0                            # 当前已连接的ws客户端数量
        self.poller = select.poll()                         # 创建poll对象
        self.clients = {}             # 保存客户端的字典:key是client_sock, value是对应的websocket
        self.on_connect = None        # 用户接口：当客户端连接到服务器时调用,参数(websocket)
        self.on_close = None          # 用户接口：当客户端关闭连接时调用,无参数
        self.on_recv = None           # 用户接口：从客户端接收到数据时调用,参数(websocket, data)
        self.on_polled = None         # 用户接口：每次轮询之后执行的回调,参数(websocket)               
        
    def _clear_sock(self,sock):                             # 清理指定的套接字（注销、关闭、删字典）
        if self.clients.get(sock,None):                     # 若有对应的WebSocket对象
            self.cur_clients_cnt=max(0,self.cur_clients_cnt-1) 
        try: self.poller.unregister(sock)                   # 从poll对象中注销
        except: pass
        try: sock.close()                                   # 关闭套接字
        except: pass
        if sock in self.clients: del self.clients[sock]     # 先判断再删除
    
    def _clear_all(self,svr_sock):                          # 清理服务器和所有客户端套接字        
        for client_sock in list(self.clients):              # 清空客户端（键转为list，避免清理时出错）
            self._clear_sock(client_sock)
        self._clear_sock(svr_sock)                          # 清理服务器套接字  
    
    def static_page(self, html=None, html_file=None):   # 注册主页或主页文件
        if html: self.html = html                           # 优先使用包含主页的str对象    
        elif html_file: self.html_file = html_file          # 其次使用文件（包含完整路径）
    
    def _http_response(self,client_sock):                   # 使用指定client_sock发送http网页响应
        html = self.html                                    # 优先使用self.html
        if not html and self.html_file:                     # 其次使用self.html_file
            with open(self.html_file,'r') as f: html = f.read()
        if not html: raise ValueError('网页内容不能为空') 
        response = f'''HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\
Content-Length: {len(html.encode())}\r\nConnection: close\r\n\r\n'''
        client_sock.setblocking(True)                       # 阻塞发送，确保完整发送响应消息
        client_sock.write(response)                         # 发送响应头
        client_sock.write(html)                             # 发送响应体
        client_sock.setblocking(False)                      # 恢复非阻塞模式
        self._clear_sock(client_sock)                       # 发送完HTTP响应后,主动清理该连接
        
    def _handshake(self,client_sock, key):                  # 处理WebSocket升级握手 
        if key is None or not client_key_valid(key):        # 验证Sec-WebSocket-Key 
            return False                                    # 握手失败
        svr_key = server_key(key)                           # 生成Sec-WebSocket-Accept
        resp = f'''HTTP/1.1 101 Switching Protocols\r\n\    # 构建升级websocket握手的响应头
Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {svr_key}\r\n\r\n'''
        client_sock.write(resp)                             # 发送响应 
        return True                                         # 握手成功

    def run(self,host='0.0.0.0', port=None, frame_type=FRAME_TXT, blocking_write=False,
            poll_timeout=50, cafile=None, keyfile=None):     # 服务器启动入口
        # host可以为ip（如192.168.1.30）或域名（如：esp32_ws_server.local）
        ctx = (cafile is not None) and (keyfile is not None) # 是否启用加密通信
        proto = 'https' if ctx else 'http'                   # 协议,开始时使用http
        if port is None: port = 443 if ctx else 80           # 若未指定端口，则使用默认端口 
        
        svr_sock = socket.socket()                           # 定义服务器TCP套接字
        svr_sock.setblocking(False)                          # 必须非阻塞
        svr_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        svr_sock.bind(('0.0.0.0', port))                     # 绑定通用接口
        svr_sock.listen(5)
        self.poller.register(svr_sock, select.POLLIN)        # 注册服务端Socket
        print(f'== {proto}://{host}:{port} 已启动==')         # 打印服务器域名
        print('[Ctrl+c退出]')
        
        while True:
            try:
                for sock,event,*_ in self.poller.ipoll(poll_timeout):  # 迭代所有就绪的套接字和事件
                    if sock is svr_sock:                               # 服务器收到连接请求
                        if self.cur_clients_cnt>=self.max_clients_cnt: # 客户端数量已达上限
                            continue 
                        clt_sock, clt_addr = svr_sock.accept()         # 接受新连接（非阻塞 ）
                        if ctx:                                        # 若加密通信，重新包装client
                            clt_sock=ssl.wrap_socket(clt_sock,server_side=True,key=keyfile,cert=cafile)
                        clt_sock.setblocking(False)                    # 客户端Socket设为非阻塞
                        self.poller.register(clt_sock, select.POLLIN)  # 注册客户端Socket的POLLIN事件
                        self.clients[clt_sock] = None                  # 该套接字对应websocket为None

                    elif event & select.POLLIN:                        # 客户端有可读数据
                        ws = self.clients[sock]                        # 获取客户端sock对应的websocket
                        if ws:                                         # 如果已升级为websocket
                            if self.on_recv: r=self.on_recv(ws)        # 执行回调
                            else: r = ws.read()                        # 使用客户端websocket读取数据
                            if not r:                                  # 无数据，客户端主动关闭
                                print('客户端主动关闭')
                                if self.on_close: self.on_close()      # 调用on_close()回调
                                self._clear_sock(sock); continue       # 清理客户端,继续遍历
                                self.cur_clients_cnt = max(0,self.cur_clients_cnt-1)
                                                            
                        else:                                          # 没有升级为websocket
                            key = None                                 # 客户端发送的Sec-WebSocket-Key
                            html_quest = False                         # 网页请求
                            while line := sock.readline():             # 客户端socket按行读取请求头                               
                                if line == b'\r\n' or not line: break  # 读到请求头末尾
                                elif b'GET / HTTP/1.1' in line:        # 网页请求
                                    html_quest=True
                                elif line.startswith(b'Sec-WebSocket-Key: '):   # websocket升级请求
                                    key = line.split(b': ')[1].decode().strip() # 提取Sec-WebSocket-Key
                                                       
                            if (not key) and (not html_quest):         # 忽略除网页和ws升级以外的请求
                                sock.write(b'HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
                                self._clear_sock(sock)                 # 清理该连接（已无用途）                                
                            elif key:                                  # 优先处理升级握手
                                if self._handshake(sock,key):          # 成功执行websocket升级握手
                                    ws=websocket(sock,blocking_write)  # 包装为websocket对象
                                    ws.ioctl(SET_FRAME_TYPE,frame_type)# 设置帧格式
                                    self.clients[sock] = ws            # 保存websocket                                 
                                    print('websocket握手成功')
                                    self.cur_clients_cnt += 1          # 客户端数量加1
                                    if self.on_connect: self.on_connect(ws)     # 调用on_connect回调
                                else:
                                    self._clear_sock(sock)             # websocket升级握手失败
                                    print('websocket升级握手失败，关闭客户端')                                
                            elif html_quest:                           # 网页请求
                                self._http_response(sock)              # 发送网页
                                
                    elif event & (select.POLLERR | select.POLLHUP):    # 客户端Socket触发错误/挂起事件                        
                        print('客户端异常(ERR/HUP)') 
                        self._clear_sock(sock)                         # 清理异常的客户端socket
                        
                if self.on_polled:                                     # 调用回调
                    for ws in self.clients.values():                   # 遍历所有websocket客户端                        
                        if ws: self.on_polled(ws)                      # 如果有对应ws对象，调用用户回调
                        
            except Exception as e:
                sys.print_exception(e)                       # 调试时打开
                if sock is svr_sock:                           # 若是服务器异常
                    print('服务器异常，断开所有连接.')
                    self._clear_all(svr_sock); break           # 清理所有套接字,退出主循环 
                else:                                          # 若是客户端异常
                    print('客户端异常或主动断开连接')
                    self._clear_sock(sock); continue           # 清理异常的客户端套接字,继续主循环                               
            except KeyboardInterrupt:                          # 键盘中断
                print('\n== 退出服务器 ==')
                self._clear_all(svr_sock); break               # 清理所有套接字,退出主循环