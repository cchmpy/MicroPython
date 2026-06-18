import asyncio
from mqtt_as import MQTTClient, config           # config是保存设置的字典对象
class AMqttConn:
    @staticmethod
    def _cb(topic, msg, retained):               # 接收消息后的回调函数（用于消息订阅）
        ...                                      # 可在此根据消息控制硬件
        print((topic.decode(), msg.decode(), retained))
        
    def __init__(self, server, ssid, wifi_pw):
        global config
        # mqtt客户端配置参数
        config['server']  = server               # MQTT 服务器地址
        config['ssid']    = ssid                 # WiFi 名称
        config['wifi_pw'] = wifi_pw              # WiFi 密码
        config['subs_cb'] = AMqttConn._cb        # 设置订阅回调函数（用于消息订阅）
        self.client = MQTTClient(config)         # 使用confgi创建客户端    
    
    async def __aenter__(self):
        await self.client.connect()              # 异步连接到mqtt代理服务器
        return self.client                       # 返回客户端（可等待对象）

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()           # 异步断开与mqtt代理服务器连接
        if exc_type is not None:                 # 如果生命周期内抛出异常
            print(exc_type,exc_val,exc_tb)
        return True                              # 已处理异常
