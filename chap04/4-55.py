from amqttconn import AMqttConn
import asyncio
async def publish_message():
    from random import randint
    async with AMqttConn('broker-cn.emqx.io', 'wifi_name', 'wifi_psw') as client: 
        while True:
            msg = f'{randint(0,100)}'            # 用随机数代表从传感器采集的数据 
            await client.publish('esp32/micropython/test', msg, retain=True)  # 发布主题、消息
            print(msg)                            # 打印提示消息
            await asyncio.sleep(10)               # 消息发送间隔  
asyncio.run(publish_message())
