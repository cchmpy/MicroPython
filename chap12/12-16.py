from bluetooth import UUID
import asyncio,aioble,random,struct

_ADV_INTERVAL_MS = 250_000
_SRV_ENV_UUID    = UUID(0x181A)
_CHAR_TEMP_UUID  = UUID(0x2A6E)
env_service = aioble.Service(_SRV_ENV_UUID)
temp_char = aioble.Characteristic(env_service, _CHAR_TEMP_UUID, read=True,read_encrypted=True)
aioble.register_services(env_service)                        # 注册服务
_encode = lambda value: struct.pack("<h", int(value * 100))  # 数据编码

async def task_sensor():         # 定期轮询硬件传感器任务，此处使用随机数模拟
    while True:        
        temp_char.write(_encode(random.randint(20,30)), send_update=False) 
        await asyncio.sleep_ms(1000)
        
async def task_broadcast():      # 广播任务，等待连接
    while True:
        print('开启广播,等待连接...')
        async with await aioble.advertise(
            _ADV_INTERVAL_MS, name='esp32_server', services=[_SRV_ENV_UUID],
        ) as connection:
            print("已连接到设备:", connection.device)
            await connection.disconnected(timeout_ms=None) 
            print('连接已断开.')

async def main():
    t1 = asyncio.create_task(task_sensor())
    t2 = asyncio.create_task(task_broadcast()) 
    await asyncio.gather(t1, t2)
asyncio.run(main())
