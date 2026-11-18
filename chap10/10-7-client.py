import asyncio
from sys import print_exception
class AsyncTCPClient:
    def __init__(self, host, port=8888, cafile=None):
        self._host = host; self._port = port        
        if cafile:
            self._ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            self._ctx.load_verify_locations(cafile=cafile) 
            self._ctx.verify_mode = ssl.CERT_REQUIRED
        else:  self._ctx = None
        self._task = self._handler = None 
        self.reader = self.writer = None # 可定义为只读属性
        
    def set_handler(self, handler):      # 设置用户自定义回调协程
        self._handler = handler

    async def _connect(self):            # 连接服务器
        if self.writer: return           # 若已经连接
        self.reader, self.writer = await asyncio.open_connection(
            self._host, self._port, self._ctx)
        print(f'已连接到{self._host}:{self._port}')

    async def _close(self):               # 关闭连接
        if self._task: self._task.cancel()
        if self.writer: 
            self.writer.close()
            await self.writer.wait_closed()
            self._task = self.reader = self.writer = None
            print('连接已关闭')

    async def _main(self):                # 回调模式入口
        self._task = asyncio.current_task()
        await self._connect()
        try:
            if self._handler:
                await self._handler(self.reader, self.writer)
        except OSError as err: print_exception(err)
        except asyncio.CancelledError:pass
        
    def run(self):
        loop = asyncio.get_event_loop()
        try: loop.run_until_complete(self._main()) 
        except KeyboardInterrupt: pass 
        finally: loop.run_until_complete(self._close())
        
    async def __aenter__(self):          # 异步上下文协议：进入接口
        await self._connect(); return self
    async def __aexit__(self, *args):    # 异步上下文协议：退出接口 
        await self._close(); return False
        
if __name__=='__main__':
    import asyncio, myutils, ssl
    from random import randint
    myutils.connect_wifi() 
    myutils.sync_ntp()
    async def handler(reader, writer):
        for i in range(10):              # 与服务器进行多次对话
            writer.write(f'Hello MPython async TCP! [{i}]\n') 
            await writer.drain()
            data = await reader.readline() 
            if data: print(data.decode().strip())
            else:  break                 # 若data为b''，服务器主动关闭了连接
            await asyncio.sleep_ms(randint(500,1500))  # 对话间隔0.5～1.5秒
    client = AsyncTCPClient(host='esp32-ec.local', port=8888, cafile='rootCA.der')
    client.set_handler(handler); 
    client.run()
