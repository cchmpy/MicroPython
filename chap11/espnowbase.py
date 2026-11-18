import network, espnow, time, json, gc
from micropython import const
from sys import print_exception
BROADCAST_MAC = const(b'\xff\xff\xff\xff\xff\xff') 
# 消息类型常量
MSG_CHAN_REQ    = const(1)                # 信道查询请求
MSG_CHAN_RESP   = const(2)                # 信道查询回复
MSG_SENSOR_DATA = const(3)                # 传感器数据上报
MSG_CONTROL_CMD = const(4)                # 下行控制指令

class ESPNowBase:                         # ESP-NOW设备基类
    @staticmethod
    def key_valid(key):                   # 判断pmk或lmk是否有效
        if isinstance(key,(bytes,bytearray,str)) and len(key)==16:
            return key
        elif key is not None: print(f'主密钥{key}无效')
        return None
    
    def __init__(self, pmk=None, lmk=None, send_retries=3, lora=False):               
        self.send_retries = send_retries  # 单播消息在链路层默认重发次数      
        self.sta=None; self.esp_now=None  # 硬件实例
        self.pmk = ESPNowBase.key_valid(pmk)
        self.lmk = ESPNowBase.key_valid(lmk)
        self.lora = lora                  # 是否设置长距离模式
        self._callbacks = {}              # 存储消息类型对应回调：{MSG1:cb1,MSG2:cb2,...}
    
    def _init_device(self):               # 硬件基础初始化
        # 恢复Wi-Fi硬件设置，避免异常行为
        sta = network.WLAN(network.STA_IF); sta.active(False)
        ap = network.WLAN(network.AP_IF); ap.active(False)
        sta.active(True)
        while not sta.active(): time.sleep(0.1)
        self.sta=sta        
        # 定义ESP-NOW对象，配置全局PMK，添加广播地址
        self.esp_now = espnow.ESPNow()
        self.esp_now.active(True)
        # 是否启用长距离传输模式
        if self.lora:
            self.sta.config(protocol=network.WLAN.PROTOCOL_DEFAULT | network.WLAN.PROTOCOL_LR)
            self.esp_now.config(rate=espnow.RATE_LORA_500K) 
        if self.pmk: self.esp_now.set_pmk(self.pmk) # 若pmk有效则设置
        self.esp_now.add_peer(BROADCAST_MAC)   
    
    def _add_peer(self, mac, encrypt=False):        # 注册对等设备
        if encrypt and self.lmk is None :           # 若加密，检查lmk是否有效
            print('lmk设置无效，无法加密通信')
            encrypt = False
        try:  self.esp_now.add_peer(mac, lmk=self.lmk, encrypt=encrypt)
        except OSError as err:
            if err.args[1] == 'ESP_ERR_ESPNOW_EXIST': pass
            elif err.args[1] == 'ESP_ERR_ESPNOW_FULL':
                print(f'注册设备已达上限，无法注册{mac}')
            else: raise err
    
    def _send_reliable(self, mac, **kwargs):         # 可靠发送，基于链路层应答自动重发
        _msg = json.dumps(dict(kwargs)).encode()     # 把关键字参数包装为JSON格式
        for _ in range(self.send_retries):           # 单播最多发送send_retries次
            try:
                if self.esp_now.send(mac, _msg, True):  return True 
            except (OSError, ValueError, TypeError) as err:                
                if err.args[0]==116: continue        # 长距离模式下可能返回OSError: [Errno 116] ETIMEDOUT
                else: print_exception(err); break
            time.sleep_ms(20)
        return False                                  # 发送send_retries次仍无响应
    
    def register_callback(self, msg_type, callback):  # 注册msg_type类型消息的回调
        self._callbacks[msg_type] = callback

    def _trigger_callback(self, msg_type, *args, **kwargs):# 调用msg_type类型消息的回调        
        cb = self._callbacks.get(msg_type,None)
        if callable(cb):          
            try: return cb(*args, **kwargs)
            except Exception as err:
                print(f'回调[{msg_type}]执行异常：')
                print_exception(err)
        return None