from mqtt_as import MQTTClient, config  # 导入第三方库
import asyncio
# 本地配置 config是全局字典变量
config['ssid']    = 'my_ssid'                                      # Wi-Fi账号
config['wifi_pw'] = 'my_key'                                       # Wi-Fi密码
config['server']  = 'broker-cn.emqx.io'
config['mqtt5']   = True                                           # 是否启用MQTT 5

async def messages(client):                                        # 定义订阅消息回调协程/响应
    async for topic, msg, retained , *_ in client.queue:
        print('收到订阅：',topic.decode(), msg.decode(), retained)

async def up(client):                                              # 重新建立连接时的回调协程
    while True:
        await client.up.wait()                                     # 等待某个事件的发生（同步方法）
        client.up.clear()
        await client.subscribe(b'sensor/数字')                     # 续订订阅服务

async def main(client):
    await client.connect()                                         # 连接服务器
    for coroutine in (up, messages):
        asyncio.create_task(coroutine(client))                     # 创建协程任务：两个回调协程
    n = 0
    while True:
        await asyncio.sleep(5)
        print('发布：sensor/数字', n)
        # 如果WiFi连接中断，那么后续的所有操作都会暂停，直到WiFi恢复连接为止
        await client.publish(b'sensor/数字', str(n).encode(), qos = 1)
        n += 1

config["queue_len"] = 1                                            # 使用具有默认队列大小的事件接口
MQTTClient.DEBUG = True                                            # 可选：打印调试信息
client = MQTTClient(config)
try:   asyncio.run(main(client))
except KeyboardInterrupt: print('断开连接')
finally: client.close() 