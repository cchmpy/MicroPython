from bluetooth import UUID
import asyncio,aioble,struct
_SRV_ENV_UUID   = UUID(0x181A)
_CHAR_TEMP_UUID = UUID(0x2A6E)
_CHAR_HUM_UUID  = UUID(0x2A6F) 
_SRV_UART_UUID  = UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
_CHAR_RX_UUID   = UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E') 
_CHAR_TX_UUID   = UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')
_decode = lambda data: struct.unpack("<h", data)[0] / 100   # 温湿度数据解码
async def find_device():                                    # 扫描并发现设备
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner: 
        async for result in scanner:
            if result.name() == "esp32_server" and _SRV_ENV_UUID in result.services():
                print(result.device); return result.device
    return None

async def main():
    aioble.config(mtu=512)                                  # 设置mtu
    device = await find_device()                            # 扫描设备
    if not device:  print("未发现设备."); return    
    try:                                                    # 连接设备
        print("连接到设备:", device)
        connection = await device.connect()
    except asyncio.TimeoutError:
        print("连接超时"); return    
    async with connection:                                  # 数据操作
        try:
            print('mtu:',await connection.exchange_mtu())                # 打印mtu交换的返回值 
            env_service = await connection.service(_SRV_ENV_UUID)        # 搜索环境感应服务
            temp_char= await env_service.characteristic(_CHAR_TEMP_UUID) # 搜索温度特性
            hum_char  = await env_service.characteristic(_CHAR_HUM_UUID) # 搜索湿度特性
            await temp_char.subscribe()  # 订阅温度特性通知,默认参数notify=True,indicate=False
            await hum_char.subscribe(notify=False,indicate=True)         # 订阅湿度特性指示
            
            uart_service = await connection.service(_SRV_UART_UUID)      # 搜索uart服务 
            rx_char = await uart_service.characteristic(_CHAR_RX_UUID)   # rx特性，可写入
            tx_char  = await uart_service.characteristic(_CHAR_TX_UUID)  # tx特性，可读取、可收通知
        except asyncio.TimeoutError:
            print("搜索服务、特性超时"); return
        while connection.is_connected():
            t = await temp_char.notified()                  # 等待温度特性通知
            h = await hum_char.indicated()                  # 等待湿度特性指示
            print('温度:',_decode(t),'湿度:',_decode(h))    # 打印温湿度信息
            data = await tx_char.notified()                 # 等待tx特性通知
            print('uart接收:',data.decode())
            await rx_char.write(data)                       # 写入rx特性
            await asyncio.sleep_ms(1000)
asyncio.run(main())