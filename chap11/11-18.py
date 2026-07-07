import asyncio, ssl
from binascii import a2b_base64
class _Response:                                          # OTAClient.get()返回的对象
    def __init__(self, reader, status, headers):
        self.reader = reader                              # 异步读取器 
        self.status = status                              # 响应状态码 
        self.headers = headers                            # 保存部分响应头字段的字典
        
    async def close(self):                                # 关闭客户端连接
        self.reader.close()                               # reader和wirter是同一对象的别名
        await self.reader.wait_closed()

class OTAClient:                                          # 客户端类
    def __init__(self, timeout=10):
        self.timeout = timeout                            # 连接服务器超时时间（秒）
   
    async def get(self, host, path, port=None, ssl=None): # 请求并解析响应头，返回_Response对象
        # 1. 异步连接服务器，发出GET请求
        if port is None: port = 443 if ssl else 80        # 定义端口
        try:
            reader, writer = await asyncio.wait_for(      # 连接服务器
                    asyncio.open_connection(host, port, ssl),
                    timeout=self.timeout)
        except (asyncio.TimeoutError,OSError) as err:
            print('× 连接服务器超时或失败,请检查服务器、主机、端口号和证书:',err) 
            return None                                   # 返回None,不返回_Response对象
        request_headers = f'GET {path} HTTP/1.1\r\nConnection: keep-alive\r\n\r\n'  # 简单请求头
        writer.write(request_headers)                     # 发送请求行和请求头
        await writer.drain() 
        
        # 2. 读取响应行、响应头，返回_Response对象
        headers = {}                                      # 保存响应头的字段
        l = await reader.readline()                       # 读取响应行 b’HTTP/1.1 200 OK\r\n
        status = int(l.split(None, 2)[1])                 # 解析状态码
        if status != 200:
            print(f'× 响应状态码[{status}]异常,请检查请求路径')
            writer.close()
            await writer.wait_closed()
            return None 
        while True:                                       # 读取响应头
            l = await reader.readline()
            if not l or l == b'\r\n': break               # 响应头结束 
            k, v = l.split(b':', 1)                       # 字段分为2部分,如Content-Type和text/html\r\n 
            k = k.strip().lower()                         # 字段名去空白，转为小写
            v = v.strip()                                 # 字段值去空白
            if k in b'content-length':                    # 保存字段Content-Length
                headers[k.decode()] = int(v)
            elif k in b'firmware-signature':              # 保存字段Firmware-Signature
                headers[k.decode()] = a2b_base64(v)       # 签名由base64字符串转为原始数据bytes            
        return _Response(reader,status,headers)           # 返回_Response对象

if __name__ == '__main__':
    from myutils import connect_wifi, sync_ntp
    async def main():                                     # 测试代码（不带参数，简化测试）
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)     # 创建客户端模式的SSLContext
        ctx.load_verify_locations(cafile='rootCA.der')    # 载入证书链数据，以验证服务器身份
        ctx.verify_mode = ssl.CERT_REQUIRED               # 验证模式:需要验证。ssl.CERT_NONE不验证
        ctx = None
        s = OTAClient(timeout=10)
        r = await s.get(host='mpy-ota.local',path='/ota', port=None, ssl=ctx)
        if r is None:  return 
        print(r.status,'\n', r.headers) 
        await r.close()     
    connect_wifi()
    sync_ntp()                                            # 更新时间，用于验证证书
    asyncio.run(main())
