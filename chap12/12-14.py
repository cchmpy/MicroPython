from bluetooth import UUID
import asyncio,aioble,random,struct
_SRV_ENV_UUID   = UUID(0x181A)
_CHAR_TEMP_UUID = UUID(0x2A6E)
_CHAR_HUM_UUID  = UUID(0x2A6F)
_DESC_UUID      = UUID(0x2901)
_SRV_UART_UUID  = UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
_CHAR_RX_UUID   = UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')
_CHAR_TX_UUID   = UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')
_ADV_INTERVAL_MS = 250_000                                   # 广播间隔时间
# 环境服务
env_service= aioble.Service(_SRV_ENV_UUID)
temp_char  = aioble.Characteristic(env_service, _CHAR_TEMP_UUID, notify=True,read=True, initial=b'')
temp_desc  = aioble.Descriptor(temp_char,_DESC_UUID, read=True, initial='客厅温度'.encode())
hum_char   = aioble.Characteristic(env_service, _CHAR_HUM_UUID,read=True, indicate=True)
hum_desc   = aioble.Descriptor(hum_char,_DESC_UUID,read=True,initial='客厅湿度'.encode())
# UART服务
uart_service = aioble.Service(_SRV_UART_UUID)
rx_char = aioble.BufferedCharacteristic(uart_service,_CHAR_RX_UUID,write=True, max_len=100,append=True)
tx_char = aioble.BufferedCharacteristic(uart_service,_CHAR_TX_UUID,read=True, notify=True,max_len=100)
# 注册服务
aioble.register_services(env_service,uart_service) 
# 全局变量
_connection = None 
_rx_buffer = bytearray()                                     # 缓存接收的数据
# ------------------------------------------------------------环境感应服务相关函数和任务
_encode = lambda value: struct.pack("<h", int(value * 100))  # 数据编码
async def task_sensor():                       # 定期轮询硬件传感器任务，使用随机数模拟
    global _connection
    while True:
        # 客户端需要订阅通知和指示，才能收到更新数据
        temp_char.write(_encode(random.randint(20,30)), send_update=True)
        hum_char.write(_encode(random.randint(0,99)), send_update=True)
        await asyncio.sleep_ms(1000)
# ------------------------------------------------------------UART服务相关函数和任务
def read_rx(size=None):                                      # 读取客户端写入的数据
    global _rx_buffer
    size = min(int(size),len(_rx_buffer)) if size else len(_rx_buffer)
    result = _rx_buffer[0:size]
    _rx_buffer = _rx_buffer[size:]
    return result

async def task_rx_capture():                                 # 捕获客户端写入数据
    global _rx_buffer
    while True:        
        connection = await rx_char.written()                 # capture = False
        _rx_buffer += rx_char.read()                         # 将接收到的数据附加到缓存末尾
        print(read_rx())                                     # 数据处理

async def task_tx_notify():                                  # 向客户端发送通知(tx)
    i = 1
    while True:
        if _connection:
            data = str(i)+'\n'
            tx_char.notify(_connection,data)
            i+=1
        await asyncio.sleep_ms(1000)
# ------------------------------------------------------------广播任务
async def task_broadcast():
    global _connection
    while True:
        print('开启广播,等待连接...')
        async with await aioble.advertise(_ADV_INTERVAL_MS, name='esp32_server',
                               services=[_SRV_ENV_UUID,_SRV_UART_UUID], ) as _connection:
            print("已连接,来自设备:", _connection.device)
            await _connection.disconnected(timeout_ms=None) # 无限等待断开
            _connection = None                              # 重置全局变量
            print('连接已断开.')
async def main():
    t1 = asyncio.create_task(task_sensor())
    t2 = asyncio.create_task(task_broadcast())
    t3 = asyncio.create_task(task_rx_capture())
    t4 = asyncio.create_task(task_tx_notify())
    await asyncio.gather(t1, t2, t3, t4)
asyncio.run(main())
