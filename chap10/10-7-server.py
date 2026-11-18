import asyncio
from sys import print_exception
class AsyncTCPServer:
    def __init__(self): 
        self._server = None                         # Server对象
        self._handler = None                        # 用户自定义回调协程
        self._tasks = set()                         # 集合保存事件循环内的所有任务
    
    def set_handler(self, handler):                 # 设置用户回调协程
        self._handler = handler
    
    async def _handle_client(self, reader, writer): # 处理单个客户端连接的协程
        task = asyncio.current_task()               # 获取当前任务 
        self._tasks.add(task)                       # 把当前任务加入集合
        try:
            addr = writer.get_extra_info('peername')# 获取客户端套接字地址
            print(f'客户端{addr}连接到服务器') 
            if self._handler:
                await self._handler(reader,writer)  # 调用用户自定义协程 
        except OSError as err: print_exception(err)
        except asyncio.CancelledError: pass         # 被其他任务取消时抛出的异常
        finally:
            self._tasks.discard(task)               # 客户端主动关闭时要把它从集合移除
            writer.close()                          # 关闭连接
            await writer.wait_closed()              # 等待连接完全关闭
            print(f'客户端{addr}连接已关闭') 
    
    async def _clear_all(self):                     # 清理、关闭客户端与服务器
        while self._tasks:
            self._tasks.pop().cancel()              # 取消所有_handle_client任务 
            await asyncio.sleep_ms(50) # 预留_handle_client中finally块的执行时间
        if self._server:
            self._server.close()                    # 关闭服务器
            await self._server.wait_closed()
            print('== 服务器已关闭 ==') 
        
    async def _main(self, host, port, ssl):         # 启动TCP服务器的主协程
        self._server = await asyncio.start_server(
            self._handle_client, host='0.0.0.0', port=port, ssl=ssl) 
        print(f'== {host}:{port} 服务器已启动==\n[Ctrl+C退出]')
        await self._server.wait_closed()            # 异步等待服务器关闭
                           
    def run(self,host='0.0.0.0',port=8888,cafile=None, keyfile=None):
        # 服务器启动入口函数
        if cafile and keyfile:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(cafile, keyfile)
        else:  ctx = None
        loop = asyncio.get_event_loop()
        try: loop.run_until_complete(self._main(host, port, ctx)) 
        except KeyboardInterrupt:pass
        finally: loop.run_until_complete(self._clear_all()) 

if __name__ == '__main__':
    from network import hostname
    import myutils, ssl
    async def handler(reader,writer):
        while True:            
            if (data:=await reader.readline()):     # 读取一行数据
                print(f'收到数据:{data}') 
                writer.write(f'服务器回显:{data.decode()}')
                await writer.drain()                # 确保数据发送完成
            else: break                             # 客户端关闭连接时，data为b''
    hostname('esp32-ec')                            # 设置主机名
    myutils.connect_wifi() 
    myutils.sync_ntp()                              # 同步时钟,用于证书校验
    srv = AsyncTCPServer()
    srv.set_handler(handler)                        # 设置回调
    srv.run(host=f'{hostname()}.local',cafile='esp32-ec.der', keyfile='esp32-ec-key.der') 
