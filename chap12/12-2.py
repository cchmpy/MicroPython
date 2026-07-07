import network, aioespnow, asyncio, json, time
from esp32 import NVS
from sys import print_exception
from micropython import const

# CI1302语音指令定义
VOICE_CMD_BEDROOM1_ON  = const(b'\xAA\x55\x00\x01\xFB')         # 主卧开灯
VOICE_CMD_BEDROOM1_OFF = const(b'\xAA\x55\x00\x02\xFB')         # 主卧关灯
VOICE_CMD_BEDROOM2_ON  = const(b'\xAA\x55\x00\x03\xFB')         # 次卧开灯
VOICE_CMD_BEDROOM2_OFF = const(b'\xAA\x55\x00\x04\xFB')         # 次卧关灯
VOICE_CMD_LIVINGROOM_ON  = const(b'\xAA\x55\x00\x05\xFB')       # 客厅开灯
VOICE_CMD_LIVINGROOM_OFF = const(b'\xAA\x55\x00\x06\xFB')       # 客厅关灯
VOICE_CMD_KITCHEN_ON   = const(b'\xAA\x55\x00\x07\xFB')         # 厨房开灯
VOICE_CMD_KITCHEN_OFF  = const(b'\xAA\x55\x00\x08\xFB')         # 厨房关灯
...
VOICE_CMD_NOT_FOUND_DEVICE  = const(b'\xAA\x55\xFF\x03\xFB')    # 被动指令：未发现设备

# 设备名称
NAME_BEDROOM1_LAMP = const('主卧灯')
NAME_BEDROOM2_LAMP = const('次卧灯')
NAME_LIVINGROOM_LAMP = const('客厅灯')
NAME_KITCHEN_LAMP = const('厨房灯')
...
# 全局变量，方便根据语音指令查找设备名称
NAME_DEVICES=(NAME_BEDROOM1_LAMP,NAME_BEDROOM2_LAMP,NAME_LIVINGROOM_LAMP,NAME_KITCHEN_LAMP)
# 消息类型定义
MSG_TYPE_DISCOVERY = const('discovery')
MSG_TYPE_DISCOVERY_ACK = const('discovery_ack')
MSG_TYPE_CONTROL = const('control')
MSG_TYPE_STATUS = const('status')
# ESP-NOW配置
BROADCAST_MAC = const(b'\xff\xff\xff\xff\xff\xff')              # 广播地址
# -----------------------------------------------------------------------------------------
class _Base:
    def __init__(self):
        # 打开射频模块，初始化AIOESPNow
        self.wlan = network.WLAN(network.WLAN.IF_STA)
        self.wlan.active(True)                                  # 打开射频模块
        self.e = aioespnow.AIOESPNow() 
        self.e.active(True)
        
    def deinit(self): 
        if self.e:    self.e.active(False)
        if self.wlan: self.wlan.active(False)
        
    async def send_espnow_message(self,mac,msg_type,msg_data):  # 发送ESP-NOW消息
        try:
            message={'msg_type': msg_type,'msg_data': msg_data} # 创建消息的字典对象
            msg_json = json.dumps(message)                      # 转为json字符串
            try: self.e.get_peer(mac)                           # 尝试获取目标设备的信息
            except OSError as err: 
                if err.errno == -12393: self.e.add_peer(mac)    # 若目标设备未注册，则添加
            await self.e.asend(mac, msg_json)                   # 异步发送
            return True
        except Exception as err:
            print_exception(err)
            return False
        
    async def handle_espnow_messages(self):                     # 抽象方法：处理接收到的消息
        raise NotImplementedError('子类必须实现handle_espnow_messages()方法')
        
    async def main(self):                                       # 抽象方法：主协程
        raise NotImplementedError('子类必须实现main()方法')
# -----------------------------------------------------------------------------------------
class Gateway(_Base):
    def __init__(self, voice_uart):
        super().__init__()                                      # 初始化基类
        # self.devices是嵌套字典对象，保存已注册设置，内容格式：
        # {mac:{'device_name':'名称','status':'unknown','rssi':-13, 'last_seen':'最近通信时间'},...}
        self.devices = {}         
        self.uart = voice_uart                                  # 连接语音识别模块的串口对象
        self.rxbuf = bytearray(5)                               # 读取串口缓冲
        self.txbuf = bytearray(b'\xAA\x55\xFF\x00\xFB')         # 写入串口缓冲 
    
    async def handle_espnow_messages(self):                     # 处理接收到的消息
        async for mac, msg in self.e:                           # 以异步迭代方式读取消息
            try:
                if msg is None: continue 
                data = json.loads(msg.decode())                 # 把消息解析为字典对象
                msg_type = data.get('msg_type')                 # 获取消息的类型
                msg_data = data.get('msg_data', {})             # 获取消息的具体数据(字典对象)                
                                
                if msg_type == MSG_TYPE_DISCOVERY:              # 设备发现类型消息
                    device_name = msg_data.get('device_name', '未命名') 
                    self.devices[mac] = {                       # 定义设备相关参数
                        'device_name': device_name,
                        'status': 'unknown',
                        'rssi': self.e.peers_table[mac][0],
                        'last_seen': self.e.peers_table[mac][1]
                    }
                    print('添加设备', self.devices[mac]) 
                    # 发送发现确认消息(消息内容任意，但不要包含mac，因为Unicode解码会出错)
                    await self.send_espnow_message(mac,MSG_TYPE_DISCOVERY_ACK, 'hello')                     
                    
                elif msg_type == MSG_TYPE_STATUS:               # 处理设备状态上报 
                    if mac in self.devices:
                        self.devices[mac]['status'] = msg_data.get('status', 'unknown')
                        self.devices[mac]['rssi'] = self.e.peers_table[mac][0],
                        self.devices[mac]['last_seen]']=self.e.peers_table[mac][1] 
            except Exception as err:
                print_exception(err)

    def get_mac_by_name(self, device_name):                     # 通过设备名称获取mac 
        for mac, device in self.devices.items():
            if device.get('device_name',None) == device_name: return mac
        self.txbuf[3] = VOICE_CMD_NOT_FOUND_DEVICE[3]           # 没有发现设备        
        self.uart.write(self.txbuf)                             # 发送语音播报提示
        return None
    
    async def handle_uart_commands(self):                       # 处理串口语音指令
        rxbuf = self.rxbuf
        status_on = {'status': 'on'}                            # 新状态字典对象，避免临时创建字典
        status_off = {'status': 'off'}
        while True:
            if self.uart.any():                
                self.uart.readinto(rxbuf)                
                if rxbuf.startswith(b'\xAA\x55\x00'):           # 判断是否为语音控制指令
                    try: name=NAME_DEVICES[ (rxbuf[3]-1)//2]    # 获取设备名称
                    except IndexError: name=None                # 索引错误
                    if name:
                        if mac:=self.get_mac_by_name(name):     # 获取设备mac
                            await self.send_espnow_message(mac,
                                MSG_TYPE_CONTROL,status_on if rxbuf[3]%2 else status_off)
            await asyncio.sleep_ms(100)

    async def main(self):                                       # 网关设备主协程
        # 创建任务，加入事件循环
        asyncio.create_task(self.handle_espnow_messages())
        asyncio.create_task(self.handle_uart_commands())
        print('ESP-NOW语音网已启动...')        
        while True: await asyncio.sleep(1) 
# -----------------------------------------------------------------------------------------
class Device(_Base):
    def __init__(self, signal, device_name):
        super().__init__()                                      # 初始化基类AIOESPNow 
        self.gw_mac = None                                      # 网关的mac
        self.signal = signal                                    # 设备的控制信号
        self.device_name = device_name                          # 设备名字
        self.device_status = 'off'                              # 设备状态
        self.signal.off()                                       # 默认关闭
   
    async def search_gateway(self):                             # 寻找网关 
        print('开始寻找网关...') 
        for i in range(10):                                     # 广播发现请求，最多尝试10次
            if self.gw_mac: return True                         # 已找到网关                                
            await self.send_espnow_message(                     # 广播消息
                BROADCAST_MAC,  MSG_TYPE_DISCOVERY,
                {'device_name': self.device_name}) 
            await asyncio.sleep(2)                              # 等待网关响应 
        print('未发现网关，将继续尝试...')
        return False
   
    async def handle_espnow_messages(self):                     # 处理接收的ESP-NOW消息
        async for mac, msg in self.e:
            try: 
                if msg is None: continue 
                data = json.loads(msg.decode())                 # 把消息解析为字典对象 
                msg_type = data.get('msg_type')                 # 获取消息的类型
                msg_data = data.get('msg_data', {})             # 获取消息的具体数据(字典对象)
                
                if msg_type == MSG_TYPE_DISCOVERY_ACK:          # 处理网关的发现确认
                    self.gw_mac = mac
                    print(f'找到网关: {mac}') 
                    await self.send_espnow_message(             # 立即上报当前状态
                        mac,  MSG_TYPE_STATUS,{'status': self.device_status})
                    
                elif msg_type == MSG_TYPE_CONTROL:              # 处理控制指令 
                    new_status = msg_data.get('status',None)
                    if new_status in ['on', 'off']: 
                        self.device_status = new_status
                        self.signal.value(1 if new_status=='on' else 0)  # 控制设备 
                        await self.send_espnow_message(         # 上报状态
                            mac,  MSG_TYPE_STATUS, {'status': self.device_status})                                        
            except Exception as err:
                print_exception(err)

    async def status_report_task(self,interval=30):             # 定期状态上报
        while True:
            if self.gw_mac:
                await self.send_espnow_message(
                    self.gw_mac,  MSG_TYPE_STATUS, {'status': self.device_status})
            await asyncio.sleep(interval)                       # 每interval秒上报一次状态

    async def main(self): 
        asyncio.create_task(self.handle_espnow_messages())      # 创建消息处理任务 
        asyncio.create_task(self.status_report_task())          # 创建定期状态上报任务
        print('设备启动成功!')  
        while True: 
            if not self.gw_mac: await self.search_gateway()     # 寻找网关 
            await asyncio.sleep(10)
