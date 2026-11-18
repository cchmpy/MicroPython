import time,myutils,ssl,json,binascii
from umqtt.simple import MQTTClient, MQTTException
from machine import unique_id, Signal, Pin

# MQTT配置
MQTT_CLIENT_ID = binascii.hexlify(unique_id())       # 需要转换为可打印字符
MQTT_SERVER = 'broker-cn.emqx.io'                    # MQTT服务器IP/域名
MQTT_PORT = 1883                                     # MQTT端口
MQTT_KEEPALIVE = 60                                  # 保活时间（秒）
MQTT_PUB_TOPIC = b'mpy_esp32/led/status'             # 发布的主题
MQTT_SUB_TOPIC = b'mpy_esp32/led/control'            # 订阅的主题control
MQTT_USER = None; MQTT_PWD = None                    # 服务器认证用户名、密码
LED = Signal(23,mode=Pin.OUT,value=0,invert=True)    # 控制LED,invert：低/高电平点亮
try:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)    # 创建客户端模式的SSLContext
    ctx.load_verify_locations(cafile='broker.emqx.io-ca.cer') # 载入证书链数据
    ctx.verify_mode = ssl.CERT_REQUIRED              # 验证服务器身份
    MQTT_PORT = 8883                                 # MQTTS端口
except: ctx = None

# 将LED状态，编码为JSON格式的bytes对象
make_msg = lambda status: json.dumps({'status':status}).encode()
# 从JSON格式的bytes对象提取LED状态
get_status = lambda msg: json.loads(msg.decode()).get('status',None)

def on_message(topic, msg):                          # 回调函数：处理订阅的消息
    print(f'\n收到消息：{topic} -> {msg}')
    status = get_status(msg)
    if status == 'on': LED.on()
    elif status == 'off': LED.off()
def main():
    try:
        # 步骤1：连接Wi-Fi，更新时间（验证服务器证书），创建MQTTClient对象
        myutils.connect_wifi(); myutils.sync_ntp()
        client=MQTTClient(client_id=MQTT_CLIENT_ID,server=MQTT_SERVER,port=MQTT_PORT,
             user=MQTT_USER, password=MQTT_PWD, keepalive=MQTT_KEEPALIVE, ssl=ctx)
        # 步骤2：设置遗嘱消息（设备异常断连时推送）
        offline_msg = make_msg('offline')
        client.set_last_will(topic=MQTT_PUB_TOPIC, msg=offline_msg,retain=True,qos=1)
        # 步骤3：设置订阅回调函数
        client.set_callback(on_message)
        # 步骤4：连接MQTT服务器（clean_session=False保留会话，timeout=5秒）
        session_present = client.connect(clean_session=True, timeout=10)
        # 步骤5：订阅主题，注意服务器可能不会保存订阅主题
        if session_present == 0 :
            client.subscribe(MQTT_SUB_TOPIC, qos=1)
            print(f'已订阅主题：{MQTT_SUB_TOPIC.decode()}')
        # 步骤6：启动主循环
        while True:
            client.check_msg()                       # 非阻塞检查服务器消息（触发回调）
            msg = make_msg('on' if LED.value() else 'off')  # 检查LED状态并包装为消息
            client.publish(topic=MQTT_PUB_TOPIC, msg=msg, retain=True, qos=1 )
            print(f'发布消息：{MQTT_PUB_TOPIC} -> {msg}')
            time.sleep(5)                            # 控制循环频率（避免高频操作）
    except KeyboardInterrupt: print('\n用户中断程序') 
    except MQTTException as e: print(f'MQTT通信异常：{e}') 
    except OSError as e: print(f'网络/系统异常：{e}') 
    # 步骤7：退出主循环，关闭连接
    finally:
        try:
            # 发布离线消息，避免服务器不支持遗嘱
            client.publish(topic=MQTT_PUB_TOPIC,msg=offline_msg,retain=True,qos=1) 
            print('断开MQTT连接...')
            client.disconnect()
        except: pass
if __name__ == '__main__':  main()

