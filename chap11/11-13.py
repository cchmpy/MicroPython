import asyncio, ssl, json
from sys import print_exception
from gc import collect
class _Request:                                                  # 保存请求消息解析结果的类
    def __init__(self):
        self.method = ''                                         # 请求方法：GET/POST/PUT等
        self.path = ''                                           # 请求路径：/api/test
        self.query= {}                                           # 请求行URL的查询参数（?后面）
        self.form = {}                                           # POST表单参数（x-www-form-urlencoded）
        self.body = b''                                          # 原始请求体（二进制） 
        self.headers={'content-length': 0, 'content-type': ''}   # 仅保存关键字段（根据需求增减）
    
    def get_header(self, name, default=None):                    # 封装获取请求头的方法（忽略大小写）
        return self.headers.get(name.lower(), default)
    
    def get_param(self, key, default=None):                      # 封装获取查询参数的方法:先form后query
        return self.form.get(key, self.query.get(key, default))
    
    def text(self):                                              # 解析请求体为纯文本（plain/html）
        try:  return self.body.decode()
        except (UnicodeDecodeError, AttributeError): return '' 
    
    def json(self):                                              # 解析请求体为JSON（application/json）        
        try:  return json.loads(self.text())                     # 先转字符串再解析JSON
        except (ValueError, TypeError): return None              # 非JSON格式时返回None，避免程序崩溃
    
class Response:                                                  # 构建和发送响应消息的类
    _STATUS_REASON = { 200: 'OK',  400: 'Bad Request',           # 常用的HTTP状态码-原因短语映射
        404: 'Not Found',500: 'Internal Server Error'}

    def __init__(self, status=200, headers=None, body=b''):      # 构造方法 
        self.status = status                                     # 状态码
        self.reason = Response._STATUS_REASON.get(status, 'OK')  # 状态码的原因短语 
        self.headers = {str(k): str(v) for k,v in headers.items()} if headers else {}     # 响应头
        
        if isinstance(body, str): self.body = body.encode()      # 响应体处理（str转bytes） 
        elif isinstance(body, (bytes,bytearray)): self.body = body
        else: raise TypeError('响应体仅支持str/bytes/bytearray对象')
        if self.body:
            if 'Content-Length' not in self.headers:             # 自动补全Content-Length（用户未指定时）
                self.headers['Content-Length'] = str(len(self.body))
            if 'Connection' not in self.headers:                 # 自动补全Connection（用户未指定时）
                self.headers['Connection'] = 'close'

    async def write(self, writer):                               # 发送响应信息
        writer.write(f'HTTP/1.1 {self.status} {self.reason}\r\n')# 写入响应行 
        for k, v in self.headers.items(): 
            writer.write(f'{k}: {v}\r\n')                        # 写入响应头
        writer.write('\r\n')                                     # 写入空行
        writer.write(self.body)                                  # 写入响应体
        await writer.drain()                                     # 等待写完
        
class Application: 
    @staticmethod
    def _parse_url_query(query):             # 解析请求行URL的查询字符串,形如'ssid=aaa&key=123'
        params = {}                                              # 保存解析结果的字典
        if not query: return params                              # 返回空字典
        for pair in query.split('&'):                            # 分割为独立的键值对列表
            if '=' in pair:                                      # 含有'=',如'ssid=aaa'
                k, v = pair.split('=', 1)                        # 只拆分第一个=，避免值内含=
                params[k] = v.replace('%20', ' ').replace('+', ' ')  # 保存键值对,URL中"%20"、"+"为空格
            elif pair.strip() != '':                             # 不含有'='非空字节串
                params[pair] = b''                               # 保存值为空的键值对
        return params
    
    @staticmethod
    async def _parse_request(reader):                            # 解析请求消息
        r = _Request()                                           # 创建保存请求信息的对象 
        # 1. 解析请求行
        l = (await reader.readline()).strip().decode()           # 解析请求行        
        if not l: return None
        #l = l.decode()
        r.method, url, _ = l.split(None,2)                       # 拆分请求行为3部分
        if '?' in url:                                           # 若是表单GET请求
            r.path, q = url.split(b'?', 1)                       # 拆分GET请求参数，如:/led/pwm?pwm=60
            r.query = Application._parse_url_query(q)            # 解析表单GET请求参数,如pwm=60&name=a
        else:  r.path = url                                      # GET请求无参数
        # 2. 解析请求头
        while True:
            l = (await reader.readline()).strip().decode()
            if not l: break                                      #  空行 
            try:
                k, v = l.split(":", 1)
                k = k.strip().lower()
                if k in {'content-length', 'content-type'}:      # 只保存2个必须字段
                    r.headers[k] = v.strip()
            except ValueError:  continue
        # 3. 解析请求体
        c_length = int(r.get_header('content-length', 0))        # 开始解析请求体，请求体长度
        c_type = r.get_header('content-type', '')                # 请求体类型
        if c_length and r.method in ('POST', 'PUT', 'PATCH'):    # 这3种方法有请求体
            r.body = await reader.readexactly(c_length)          # 准确读取请求体
            if 'application/x-www-form-urlencoded' in c_type:    # 请求体是表单POST方法提交数据
                r.form = Application._parse_url_query(r.text()) 
        return r
    
    def __init__(self):                                          # 类的构造方法 
        self._routes = {}                                        # 路由注册字典,存储{路径: 异步回调函数}         
    
    def add_route(self, path, handler):                          # 路由绑定：请求路径与异步处理函数
        np = path.rstrip('/') if path != '/' else '/'            # 标准化路径（去掉末尾/，如/led/set/）
        self._routes[np] = handler
    
    def add_routes(self,routes):                                 # 批量路由绑定routes=[(path,handler),]
        for path, handler in routes: self.add_route(path, handler)
        
    async def _404_handler(self,request):                        # 404回调：路径未匹配时调用
        return Response(status=404, headers={'Content-Type': 'text/plain; charset=utf-8'},
                        body='404 Not Found（页面不存在）')

    async def _500_handler(self,request):                        # 500回调：服务器错误时调用
        return Response(status=500, headers={'Content-Type': 'text/plain'},
                        body='500 Internal Server Error')
    
    async def _handle_client(self,reader, writer):               # 处理单个客户端连接的协程函数
        try:
            request = await Application._parse_request(reader)   # 解析客户端请求
            if not request: return
            handler=self._routes.get(request.path,self._404_handler) # 匹配路由回调
            try: 
                response = await handler(request)                # 调用路由回调，返回Response对象
                await response.write(writer)                     # 发送响应消息 
            except Exception as err:                             # 执行回调出现错误
                print_exception(err)                             # 打印回调执行时的错误
                response = await self._500_handler(request)      # 服务器错误响应对象
                await response.write(writer)                     # 发送响应消息
        except Exception as err:
            if err.errno != -30592:                              # 忽略ssl证书不匹配错误
                print_exception(err)
        finally: 
            writer.close()                                       # 关闭连接
            await writer.wait_closed()                           # 等待连接完全关闭
            collect()                                            # 手动垃圾回收 
    
    async def _main(self, host, port, ssl):                      # 启动服务器的主协程 
        self._server = await asyncio.start_server(self._handle_client, host=host, port=port, ssl=ssl)        
        proto = 'https' if ssl else 'http'
        print(f'== {proto}://{host}:{port} 已启动==')            # 打印服务器域名
        print('[Ctrl+c退出]')
        await self._server.wait_closed()                         # 异步等待服务器关闭
    
    def run(self,host='0.0.0.0', port=None, cafile=None, keyfile=None): # 服务器启动入口函数
        if cafile and keyfile:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)        # 定义SSLContext对象
            ctx.load_cert_chain(cafile, keyfile)
        else:  ctx = None
        if port is None: port = 443 if ctx else 80               # 若未指定端口，则使用默认端口
        try: asyncio.run(self._main(host, port, ctx))
        except KeyboardInterrupt:
            if self._server: self._server.close()

if __name__ == '__main__':
    from network import hostname
    import myutils       
    wlan=myutils.connect_wifi()
    myutils.sync_ntp()    
    app = Application()
    async def index(request):
        return Response(headers={'Content-Type': 'text/plain; charset=utf-8'},body='这是测试页面')
    app.add_route('/',index)    
    app.run(host=wlan.ifconfig()[0])
