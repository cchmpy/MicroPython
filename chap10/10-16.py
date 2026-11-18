from mqtt_as import MQTTClient, config             # 导入第三方库
import asyncio, ssl, json
from machine import unique_id, Signal, Pin

MQTT_PUB_TOPIC = b'mpy_esp32/led/status'           # 发布的主题
MQTT_SUB_TOPIC = b'mpy_esp32/led/control'          # 订阅的主题control
LED = Signal(23,mode=Pin.OUT,value=0,invert=True)
# 本地配置config是全局字典对象，默认：config['client_id']=hexlify(unique_id())
config['ssid']    = 'ssid'                         # 用户的Wi-Fi账号
config['wifi_pw'] = 'psw'                          # 用户的Wi-Fi密码
config['server']  = 'broker-cn.emqx.io'
config['port']    = 1883
config['mqtt5']   = False                          # 是否启用MQTT 5
config['ssl']     = False
config['ssl_params'] = {}  
config['queue_len'] = 1                            # 使用具有默认队列大小的事件接口
    
# 将LED状态，编码为JSON格式的bytes对象
make_msg = lambda status: json.dumps({'status':status}).encode()
# 从JSON格式的bytes对象提取LED状态
get_status = lambda msg: json.loads(msg.decode()).get('status',None)

async def messages(client):                        # 定义订阅消息回调协程/响应
    async for topic, msg, retained , *_ in client.queue:        
        print(f'\n收到消息：{topic} -> {msg}')
        status = get_status(msg)
        if status == 'on': LED.on()
        elif status == 'off': LED.off()
        
async def up(client):                              # 重新建立连接时的回调协程
    while True:
        await client.up.wait()                     # 等待某个事件的发生（同步方法）
        client.up.clear()
        await client.subscribe(MQTT_SUB_TOPIC, 1)  # 续订订阅服务
        
async def main(client):
    await client.connect()                         # 连接服务器
    for coroutine in (up, messages):
        asyncio.create_task(coroutine(client))     # 创建协程任务：两个回调协程    
    while True:         
        msg = make_msg('on' if LED.value() else 'off')
        # 如果Wi-Fi连接中断，那么后续的所有操作都会暂停，直到Wi-Fi恢复连接为止
        await client.publish(MQTT_PUB_TOPIC, msg, qos = 1)    
        print(f'发布消息：{MQTT_PUB_TOPIC} -> {msg}')
        await asyncio.sleep(5)
              
MQTTClient.DEBUG = True                            # 可选：打印调试信息
client = MQTTClient(config)
try:   asyncio.run(main(client))
except KeyboardInterrupt: print('断开连接')
finally: client.close()


