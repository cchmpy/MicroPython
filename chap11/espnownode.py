from espnowbase import *          # 导入程序11-2.py
class ESPNowNode(ESPNowBase):    
    # 2.4GHz信道列表，常用信道前置以加快扫描速度
    CHANNELS = [1, 6, 11, 2, 3, 4, 5, 7, 8, 9, 10, 12, 13]    
    _instance = None    
    def __new__(cls, *args, **kwargs): 
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, pmk=None, lmk=None, node_id='node01',
                 encrypt=False, interval_ms=5000,
                 send_retries=3, scan_timeout_ms=50, lora=False):           
        super().__init__(pmk, lmk, send_retries, lora)
        self.node_id = node_id               # 本节点唯一标识
        self.encrypt = encrypt               # 是否加密通信
        self.scan_timeout_ms=scan_timeout_ms # 单信道扫描等待回复超时
        self.interval_ms = interval_ms       # 上报传感器的时间间隔
        self.gateway_mac = None              # 网关地址
        req_msg = {'type':MSG_CHAN_REQ, 'node_id':node_id, 'encrypt':encrypt}
        self.req_msg = json.dumps(req_msg).encode()    # 扫描信道消息

    def scan_gateway(self):          # 遍历所有信道查找网关，自动切换信道/保存网关mac
        print('启动网关信道扫描 ...')        
        for chan in ESPNowNode.CHANNELS:          # 遍历信道            
            self.sta.config(channel=chan)         # 设置信道
            time.sleep_ms(10)                     # 等待射频硬件切换稳定
            print(f'\r尝试信道{chan:2d}...', end=' ')
            try:
                self.esp_now.send(BROADCAST_MAC, self.req_msg)
                gateway_mac, msg = self.esp_now.irecv(self.scan_timeout_ms)
            except (OSError, ValueError, TypeError) as err:
                print_exception(err); continue            
            if msg is None:
                print('超时无响应', end=''); continue                
            try:
                msg_obj = json.loads(msg)
                if msg_obj.get('type') == MSG_CHAN_RESP:
                    resp_chan = msg_obj['channel']
                    print(f'\n找到网关，信道{resp_chan}')
                    gateway_mac = bytes(gateway_mac)           # bytearray→bytes
                    self._add_peer(gateway_mac, self.encrypt)  # 注册网关，若加密将检查lmk
                    if self.gateway_mac != gateway_mac:
                        self.gateway_mac = gateway_mac         # 保存网关mac
                    return True
            except (ValueError, KeyError) as err:
                print_exception(err); continue   
        print('\n扫描完成，未找到网关')
        return False
    
    def run(self):        
        self._init_device()                # 初始化设备
        self.sta.config(reconnects=0)      # 禁用后台自动扫描，避免干扰ESP-NOW
        print(f'=== 节点{self.node_id}已启动 ===')
        while True:
            if self.scan_gateway(): break  # 扫描网关
            print('3秒后重试...')
            time.sleep(3)
        imme_send = False                  # 设置硬件后立即发送状态信息
        interval = self.interval_ms        # 用局部变量缓存实例变量
        start = time.ticks_ms()            # 上报传感器数据的开始时间
        while True:
            try:
                # 1. 发送{'type': MSG_SENSOR_DATA, 'node_id':str, 'data':{双方约定}}
                now = time.ticks_ms()
                if imme_send or time.ticks_diff(now, start)>=interval:
                    start = now
                    _msg = self._trigger_callback(MSG_SENSOR_DATA) # 获取用户组装的传感器数据
                    print(f'发送传感器数据{_msg}')
                    assert  isinstance(_msg, dict)
                    if not self._send_reliable(self.gateway_mac, type=MSG_SENSOR_DATA,
                                               node_id=self.node_id, data=_msg): 
                        self.scan_gateway() # 发送失败，寻找网关和信道
                    imme_send = False       # 恢复正常发送频率
                    gc.collect()            # 垃圾回收时间间隔self.interval_ms
                    
                # 2. 接收网关发送的控制指令：{'type': MSG_CONTROL_CMD, 'cmd':{双方约定}}
                if self.esp_now.any():
                    gateway_mac, msg = self.esp_now.irecv(0)
                    msg = json.loads(msg)
                    print(f'接收了网关发送的消息{msg}')
                    # 确定是网关发送的控制消息指令
                    if gateway_mac == self.gateway_mac and msg['type']== MSG_CONTROL_CMD:
                        if (cmd_msg := msg.get('cmd')):
                            self._trigger_callback(MSG_CONTROL_CMD, json.loads(cmd_msg))
                            imme_send = True; continue             # 立即发送硬件状态信息   
                    else: print('未知类型消息')
                time.sleep(0.2)                
            except KeyboardInterrupt: break
        self.esp_now.active(False)
        self.sta.active(False)
        print(f'=== 节点{self.node_id}退出')

if __name__ == '__main__':
    from machine import Signal, Pin
    led = Signal(4,mode=Pin.OUT,value=0,invert=True)   # 节点为LED灯
    node = ESPNowNode(pmk=b'1234'*4, lmk=b'abcd'*4,
                      node_id='LED', encrypt=True,
                      scan_timeout_ms=100, lora=True)
    # 定义并注册MSG_SENSOR_DATA消息类型的回调    
    def sensor_data_cb():                    # 读取传感器数据并返回字典对象
        status = 'on' if led.value() else 'off'
        return {'status': status}            # 与网关约定的格式
    node.register_callback(MSG_SENSOR_DATA, sensor_data_cb)
    # 定义并注册MSG_CONTROL_CMD消息类型的回调
    def control_cmd_cb(cmd_msg):    # 根据消息控制硬件
        node_id = cmd_msg.get('node_id')     # 由于测试APP未实现该键值，所以总是None 
        status = cmd_msg.get('status')
        if status == 'on': led.on()
        elif status == 'off': led.off()
    node.register_callback(MSG_CONTROL_CMD, control_cmd_cb)
    node.run()                               # 启动ESP-NOW节点
