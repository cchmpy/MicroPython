import ssl,binascii
from umqtt.simple import MQTTClient, MQTTException
from myutils import connect_wifi, sync_ntp
from machine import unique_id
from espnowbase import *           # 导入程序11-2.py 

# MQTT Broker配置
MQTT_CLIENT_ID = binascii.hexlify(unique_id())       # 需要转换为可打印字符
MQTT_SERVER = 'broker-cn.emqx.io'                    # MQTT服务器IP/域名
MQTT_PORT = 0                                        # MQTT端口
MQTT_KEEPALIVE = 60                                  # 保活时间（秒）
MQTT_PUB_TOPIC = b'mpy_esp32/led/status'             # 发布的主题
MQTT_SUB_TOPIC = b'mpy_esp32/led/control'            # 订阅的主题control
MQTT_USER = None; MQTT_PWD = None                    # 服务器认证用户名、密码
LAST_WILL_MSG = b'{"status":"offline"}'              # 遗嘱消息

class ESPNowGateway(ESPNowBase):  # ESP-NOW网关：Wi-Fi+ESP-NOW双栈，自动适配路由器跳信道    
    _instance = None    
    @staticmethod
    def ssl_context(cafile):      # 用证书文件cafile定义SSLContext对象
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.load_verify_locations(cafile='broker.emqx.io-ca.cer') 
            ctx.verify_mode = ssl.CERT_REQUIRED             
        except Exception: ctx = None
        return ctx
    
    def __new__(cls, *args, **kwargs): # 单例对象
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance 

    def __init__(self, pmk=None, lmk=None, send_retries=3, lora=False):       
        super().__init__(pmk, lmk, send_retries, lora)
        self.node_mac = {}         # 节点名称对应的mac地址：{node_id:[mac1]}
        self.client = None         # MQTT客户端
    
    def _on_mqtt_msg(self, topic, msg):  # 回调函数：处理订阅的消息        
        msg_obj = json.loads(msg)
        node_id = msg_obj.get('node_id') # 获取消息中的node_id
        if node_id is None: node_id='LED'# 若消息没有node_id键，使用'LED'        
        # 把订阅消息包装为控制消息,向所有名为node_id节点发送
        # 消息格式：{'type': MSG_CONTROL_CMD, 'cmd':{双方约定}} 
        for mac in self.node_mac.get(node_id,[]): # 根据node_id获取节点mac地址
            self._send_reliable(mac, type=MSG_CONTROL_CMD, cmd=msg)
            print(f'向 {node_id} 发出控制指令 {msg}')
           
    def _connect_broker(self, ssl_ctx):   # 连接MQTT Broker     
        try:
            self.client=MQTTClient(client_id=MQTT_CLIENT_ID, server=MQTT_SERVER,
                                   port=MQTT_PORT, user=MQTT_USER, password=MQTT_PWD,
                                   keepalive=MQTT_KEEPALIVE, ssl=ssl_ctx)
            self.client.set_last_will(topic=MQTT_PUB_TOPIC, msg=LAST_WILL_MSG,
                                      retain=True, qos=1)  # 设置遗嘱消息
            self.client.set_callback(self._on_mqtt_msg)    # 设置订阅消息的回调函数
            sp = self.client.connect(clean_session=True, timeout=10) # 连接服务器
            if sp == 0: self.client.subscribe(MQTT_SUB_TOPIC, qos=1) # 订阅主题
            return True
        except (MQTTException, OSError) as err:
            print_exception(err); return False
            
    # 网关启动入口：run
    def run(self, wifi_ssid, wifi_psw, broker_cafile=None):  
        self._init_device()                  # 调用基类方法，初始化硬件        
        connect_wifi(wifi_ssid, wifi_psw); sync_ntp()
        self.sta.config(pm=self.sta.PM_NONE) # 禁用节能模式，保证ESP-NOW接收稳定
        print(f'Wi-Fi连接成功，当前信道: {self.sta.config("channel")}')
        ssl_ctl = None
        if broker_cafile is not None:
            ssl_ctl = ESPNowGateway.ssl_context(broker_cafile)
        if self._connect_broker(ssl_ctl):
            print(f'连接Broker[{MQTT_SERVER}]成功')
        else: print(f'连接Broker[{MQTT_SERVER}]失败')
        print(f'=== 网关已启动 MAC: {self.sta.config("mac")} ===')
        
        while True:
            try:
                gc.collect()
                time.sleep(0.2) 
                # 1. 非阻塞检查订阅消息，触发回调_on_mqtt_msg
                self.client.check_msg() 
                # 2. 接收ESP-NOW消息，也可用poll轮询
                if not self.esp_now.any(): continue
                try: node_mac, msg = self.esp_now.irecv(50)
                except OSError as err:
                    print_exception(err); continue 
                if msg is None: continue
                # 2.1 解析JSON格式的msg
                try:             
                    msg_obj = json.loads(msg)
                    msg_type = msg_obj.get('type')              # 消息类型
                    node_id = msg_obj.get('node_id','unknown')  # 节点名称
                except (ValueError, KeyError):
                    print(f'来自{node_mac}]消息{msg}格式错误，已忽略')
                    continue                 
                # 2.2 消息分发处理
                if msg_type == MSG_CHAN_REQ:     # 收到信道查询
                    # 接收消息格式：{'type':MSG_CHAN_REQ, 'node_id':str, 'encrypt':bool}
                    # 回复：{'type': MSG_CHAN_RESP, 'channel':uint}                    
                    self._add_peer(node_mac, False)   # 必须非加密注册节点,因为对端不能添加节点
                    chan = self.sta.config('channel')
                    self._send_reliable(node_mac, type=MSG_CHAN_RESP, channel=chan)
                    print(f'向 {node_id} 回复了当前网关的地址和信道')
                    if msg_obj.get('encrypt',False):  # 是否加密，若加密修改注册信息
                        self.esp_now.mod_peer(node_mac,lmk=self.lmk,encrypt=True)       
                    # 保存node_id对应的mac                              
                    nodes = self.node_mac.get(node_id,[])
                    if len(nodes)==0:                  # 还没保存设备node_id的mac
                        self.node_mac[node_id] = nodes # 新增键值对node_id:[]
                    if node_mac not in nodes:          # node_mac地址不在列表内
                        nodes.append(node_mac)                       
                    
                elif msg_type == MSG_SENSOR_DATA:  # 收到传感器数据
                    # 接收消息格式：{'type': MSG_SENSOR_DATA, 'node_id':str, 'data':{双方约定}}
                    msg_data = msg_obj.get('data')
                    # 调用消息类型MSG_SENSOR_DATA的回调
                    self._trigger_callback(msg_type, node_id, msg_data)
                    # 发布主题。消息内添加设备名称键值对，例如{'node_id':str, 'status':'on'}
                    msg_data['node_id']=node_id    
                    self.client.publish(topic=MQTT_PUB_TOPIC,
                                        msg=json.dumps(msg_data).encode(),
                                        retain=True, qos=1 )
                    print(f'发布主题{MQTT_PUB_TOPIC}消息：{msg_data}')                    
                else:
                    print(f'未知类型消息:', node_mac, msg_obj)                    
            except KeyboardInterrupt: break
        self.esp_now.active(False)
        self.sta.active(False)
        print('=== 网关已关闭 ===')
        
if __name__ == '__main__':
    # 此处配置MQTT Broker的全局变量，如 MQTT_SERVER。这里使用默认值
    gateway = ESPNowGateway(pmk=b'1234'*4, lmk=b'abcd'*4, lora=True)    
    def sensor_data_cb(node_id, msg_data): # 收到传感器数据时的回调
        print(f'收到 {node_id} 的数据：{msg_data}')      
    gateway.register_callback(MSG_SENSOR_DATA, sensor_data_cb)
    gateway.run(wifi_ssid='CMCC-7LhU', wifi_psw='8c8yzcb5',
                broker_cafile='broker.emqx.io-ca.cer')
