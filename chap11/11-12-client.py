import asyncio, myutils, ssl
from random import randint

async def tcp_client():                                    # 定义客户端协程
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)          # 创建客户端模式的SSLContext
    ctx.load_verify_locations(cafile='rootCA.der')         # 载入证书链数据，以验证服务器身份
    ctx.verify_mode = ssl.CERT_REQUIRED                    # 验证模式:需要验证
    
    # 异步连接服务器
    reader, writer = await asyncio.open_connection(host='esp32-ec.local', port=8888, ssl = ctx)
    for i in range(20):                                    # 与服务器进行多次对话
        writer.write(f'Hello MPython async TCP! [{i}]\n')  # 发送数据到服务器
        await writer.drain()                               # 确保数据发送完成        
        data = await reader.readline()                     # 异步读取服务器回显数据
        print(f'收到服务器回显: {data.decode().strip()}')
        await asyncio.sleep_ms(randint(500,3000))          # 等待0.5～3秒
    
    print("关闭客户端连接")
    writer.close()
    await writer.wait_closed()

if __name__ == '__main__':
    import myutils    
    myutils.connect_wifi()                                 # 连接Wi-Fi
    myutils.sync_ntp()                                     # 同步时钟
    asyncio.run(tcp_client())                              # 启动事件循环
