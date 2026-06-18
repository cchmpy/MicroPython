from amqttconn import AMqttConn
import asyncio

async def subscribe_example():
    async with AMqttConn('broker-cn.emqx.io', 'wifi_name', 'wifi_psw') as client:
        await client.subscribe('esp32/micropython/test')    # 订阅主题，接收消息后自动调用回调函数
        while True:            
            await asyncio.sleep(5)
asyncio.run(subscribe_example())
