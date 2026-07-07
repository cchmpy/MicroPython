import time,myutils,ssl
from umqtt.simple import MQTTClient, MQTTException
from machine import unique_id, Signal,Pin

# MQTT配置
MQTT_CLIENT_ID = unique_id()                                        # 唯一客户端ID
MQTT_SERVER = 'broker-cn.emqx.io'                                   # MQTT服务器IP/域名
MQTT_PORT = 1883                                                    # MQTT端口
MQTT_KEEPALIVE = 60                                                 # 保活时间（秒）
MQTT_PUB_TOPIC = b'mpy_esp32/led/status'                            # 发布的主题
MQTT_SUB_TOPIC = b'mpy_esp32/led/control'                           # 订阅的主题control
MQTT_USER = None                                                    # 服务器认证用户名
MQTT_PWD = None                                                     # 服务器认证密码
LED = Signal(23,mode=Pin.OUT,value=0,invert=True)                   # 控制LED,invert控制低/高电平点亮

try:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)                   # 创建客户端模式的SSLContext
    ctx.load_verify_locations(cafile='DigiCert Global Root G2.der') # 载入证书链数据
    ctx.verify_mode = ssl.CERT_REQUIRED                             # 验证服务器身份
    MQTT_PORT = 8883                                                # MQTTS端口
except: ctx = None 

def on_message(topic, msg):                                         # 回调函数：处理订阅的消息
    print(f'\n收到消息：{topic} -> {msg}')
    if msg == b'on':    LED.on()
    elif msg == b'off': LED.off()

def main():
    try:
        # --------步骤1：连接WiFi，更新时间（验证服务器证书）
        myutils.connect_wifi()
        myutils.sync_ntp()
        # --------步骤2：创建MQTTClient对象
        client = MQTTClient(client_id=MQTT_CLIENT_ID, server=MQTT_SERVER, port=MQTT_PORT,
                            user=MQTT_USER, password=MQTT_PWD, keepalive=MQTT_KEEPALIVE, ssl = ctx)
        # --------步骤3：可选 - 设置遗嘱消息（设备异常断连时推送）
        client.set_last_will( topic=MQTT_PUB_TOPIC, msg=b'offline', retain=True, qos=1)
        # --------步骤4：设置订阅回调函数
        client.set_callback(on_message)
        # --------步骤5：连接MQTT服务器（clean_session=False保留会话，timeout=5秒）
        session_present = client.connect(clean_session=False, timeout=10)
        # --------步骤6：订阅主题，注意服务器可能不会保存订阅主题
        if session_present == 0 :
            client.subscribe(MQTT_SUB_TOPIC, qos=1)
            print(f'已订阅主题：{MQTT_SUB_TOPIC.decode()}')
        # --------步骤7：启动主循环
        while True:
            client.check_msg()                                       # 非阻塞检查服务器消息（触发回调）
            status = b'on' if LED.value() else b'off'                # 检查LED状态
            client.publish(topic=MQTT_PUB_TOPIC, msg=status, retain=True, qos=1 )
            print(f'发布消息：{MQTT_PUB_TOPIC} -> {status}')
            time.sleep(5)                                            # 控制循环频率（避免高频操作）
    except KeyboardInterrupt: print('\n用户中断程序')                # 捕获键盘中断（Ctrl+c）
    except MQTTException as e: print(f'MQTT通信异常：{e}')           # 捕获MQTT相关异常
    except OSError as e: print(f'网络/系统异常：{e}')                # 捕获其他异常
    # --------步骤8：退出主循环，关闭连接
    finally:
        try:
            client.publish(topic=MQTT_PUB_TOPIC, msg=b'offline', retain=True, qos=1) # 避免服务器不支持遗嘱消息
            print('断开MQTT连接...')
            client.disconnect()
        except: pass
if __name__ == '__main__':  main()
