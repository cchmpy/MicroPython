from bluetooth import UUID
import asyncio,aioble,struct
_SRV_ENV_UUID   = UUID(0x181A)
_CHAR_TEMP_UUID  = UUID(0x2A6E)
_decode = lambda data: struct.unpack("<h", data)[0] / 100  # 温度数据解码

async def find_device():                    # 扫描并发现设备
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner: 
        async for result in scanner:  
            if result.name() == 'esp32_server' and _SRV_ENV_UUID in result.services():
                print(result.device)
                return result.device
    return None

async def main(): 
    device = await find_device()             # 扫描设备
    if not device: print("未发现设备"); return
    try:                                     # 连接设备
        print("连接到设备:", device)
        connection = await device.connect()
    except asyncio.TimeoutError:
        print("连接超时");  return    
    async with connection:                   # 数据操作
        try:
            # await connection.pair()        # 可以在此发起配对
            env_service = await connection.service(_SRV_ENV_UUID) 
            temp_char = await env_service.characteristic(_CHAR_TEMP_UUID) 
        except asyncio.TimeoutError:
            print("搜索服务或特性超时") 
        while connection.is_connected():
            try: t = await temp_char.read()  # 读取特性值
            except aioble.GattError as exc:               
                if exc.errno in (261,271):   # 若特性有加密读要求（错误码为261或271）
                    print('发起配对...')
                    await connection.pair()  # 发起配对
            else: print('温度:',_decode(t))   # 打印温度信息
            await asyncio.sleep_ms(1000)
            
asyncio.run(main())
