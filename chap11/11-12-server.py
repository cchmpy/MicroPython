import asyncio
class ATCPServer:
    def __init__(self, ip=''):                          # 类的构造方法
        self._ip = ip                                   # 服务器ip地址或域名
        self._server = None                             # 异步服务器对象

    async def _handle_client(slef,reader, writer):      # 处理单个客户端连接的协程函数
        addr = writer.get_extra_info('peername')        # 获取客户端套接字地址（IP+端口）
        print(f'新客户端连接:{addr}')
        try:
            while True:
                data = await reader.readline()          # 读取一行数据
                if not data:                            # 客户端关闭连接时，data为空
                    print(f'客户端{addr}断开连接')
                    break
                msg = data.decode().strip()
                print(f'收到{addr}的数据:{msg}') 
                writer.write(f'服务器回显:{msg}\n')     # 向客户端写入回显数据
                await writer.drain()                   # 确保数据发送完成
        except OSError as err:
            print(f'处理客户端{addr}出现异常: {err}')
        finally:
            writer.close()                              # 关闭连接
            await writer.wait_closed()                  # 等待连接完全关闭
            print(f'客户端{addr}连接已关闭')

    async def _main(self, host, port, ssl):             # 启动TCP服务器的主协程 
        self._server = await asyncio.start_server(
            self._handle_client, host=host, port=port, ssl=ssl)
        print(f'{self._ip}服务器已启动...')              # 打印服务器ip地址
        await self._server.wait_closed()                # 异步等待服务器关闭
 
    def run(self,host='0.0.0.0', port=8888, ssl=None):  # 服务器启动入口函数
        asyncio.run(self._main(host, port, ssl))
        
    def close(self):                                    # 关闭服务器
         if self._server: 
            self._server.close()
            print('服务器已停止')

if __name__ == '__main__':
    from network import hostname
    import myutils, ssl
    host = 'esp32-ec'
    hostname(host)                                      # 设置主机名
    myutils.connect_wifi()                              # 连接Wi-Fi
    myutils.sync_ntp()                                  # 同步时钟,用于证书校验
    try:
        ssl_ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER) # 创建服务器模式的SSLContext对象
        ssl_ctx.load_cert_chain('esp32-ec.der', 'esp32-ec-key.der') # 加载服务器证书和私钥数据
        tcp_srv = ATCPServer(f'{host}.local')           # 创建服务器对象
        tcp_srv.run(ssl=ssl_ctx)                        # 启动服务器
    except KeyboardInterrupt:
        tcp_srv.close()
        print('服务器被手动终止')
