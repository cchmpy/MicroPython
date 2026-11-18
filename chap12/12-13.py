import time,struct,random,bluetooth as BT
from bluetooth import UUID
from micropython import const
from blesec import BleSec                      # 导入程序13-11.py（blesec.py）
from ble_advertising import decode_name        # 导入程序13-2.py（ble_advertising.py）
_IRQ_SCAN_RESULT                = const(5)
_IRQ_SCAN_DONE                  = const(6) 
_IRQ_PERIPHERAL_CONNECT         = const(7) 
_IRQ_PERIPHERAL_DISCONNECT      = const(8) 
_IRQ_GATTC_CHARACTERISTIC_RESULT= const(11) 
_IRQ_GATTC_CHARACTERISTIC_DONE  = const(12)
_IRQ_GATTC_READ_RESULT          = const(15)
_IRQ_GATTC_READ_DONE            = const(16)
_IO_CAPABILITY_KEYBOARD_DISPLAY = const(4)     # 设备I/O能力
_CHAR_UUID = UUID(0x2A6E)                      # 温度特性uuid

class BleClient(BleSec):
    def __init__(self,*,srv_name='esp32_temp',json_file='secrets_clt.json',le_secure=True,mitm=False):
        super().__init__(json_file)            # 初始化父类
        self._load_secrets()                   # 把已保存的密钥载入到字典
        self._srv_name = srv_name              # 待连接服务器的名字 
        self._ble.irq(self._irq); self._ble.active(True)
        self._ble.config(bond=True,le_secure=le_secure,mitm=mitm,io=_IO_CAPABILITY_KEYBOARD_DISPLAY)
        self._found = None; 
        self._conn_h   = None                  # 与服务器的连接句柄
        self._temp_handle,self._temp_data,self._status = None,None,None  # 值句柄、读取结果、读取状态
        self._has_read = None                  # 是否完成读取
        self._ble.gap_scan(3000,500_000, 200_000, True)  
   
    def _irq(self,event, data):
        # ----------------------------------------------------------扫描
        if event == _IRQ_SCAN_RESULT:          # 事件：扫描到一个数据包
            addr_type, addr, _, _, adv_data = data            
            if decode_name(bytes(adv_data))==self._srv_name:            
                self._found = True                
                self._ble.gap_connect(addr_type, addr)  # 发起连接
        elif event == _IRQ_SCAN_DONE:
            print('触发事件:_IRQ_SCAN_DONE','本次扫描已经完成或者被停止.')
            if self._found is None:
                self._found = False
                print(f'没有发现设备{self._srv_name}。') 
        # ----------------------------------------------------------连接 
        elif event == _IRQ_PERIPHERAL_CONNECT:
            self._conn_h, _, addr = data 
            print('触发事件:_IRQ_PERIPHERAL_CONNECT','本地中央设备(客户端)已连接到服务器.')
            self._cnt_get,self._cnt_set=0,0
            self._ble.gattc_discover_characteristics(self._conn_h,1,0xffff,_CHAR_UUID) # 开始搜特性
        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, _, addr = data 
            print('触发事件:_IRQ_PERIPHERAL_DISCONNECT','本地中央设备(客户端)已与服务器断开连接.') 
        # ----------------------------------------------------------搜索特性
        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:   # 搜索到一个特性
            conn_handle, end_handle, value_handle, properties, uuid = data
            if uuid == _CHAR_UUID: self._temp_handle = value_handle
        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:     # 特性搜索完成
            conn_handle, status = data
            if self._temp_handle is not None: self._has_read = False 
        # ----------------------------------------------------------读取    
        elif event == _IRQ_GATTC_READ_RESULT:              # 读取结果
            conn_handle, value_handle, char_data = data 
            self._temp_data = bytes(char_data)
        elif event == _IRQ_GATTC_READ_DONE:                # 读取完成
            conn_handle, value_handle, self._status = data # 保存读取返回状态status
            self._has_read = True
        else:
            return self._security_irq(event, data)         # 安全事件处理回调函数
            try:                                           # 当取消配对时，进行异常处理
                return self._security_irq(event, data)     # 安全事件处理回调函数
            except OSError:
                self._ble.gap_disconnect(self._conn_h)
            
    def pair(self):
        self._ble.gap_pair(self._conn_h)                   # 发起配对
        while True:                                        # 等待完成配对
            if self._encrypted: return     # _IRQ_ENCRYPTION_UPDATE事件被触发，加密完成
            time.sleep_ms(10)
            
    def found_device(self):                                # 是否发现设备
        while self._found is None: time.sleep_ms(10)       # 等待扫描完成
        return self._found
    
    def read(self):
        while self._has_read is None: time.sleep_ms(10)    # 等待特性搜索完成
        self._temp_data,self._status = None,None
        self._ble.gattc_read(self._conn_h,self._temp_handle)# 读取结果
        while not self._has_read: time.sleep_ms(10)        # 等待读取完成
        self._has_read=False
        return self._status, self._temp_data
    
    def deinit(self):
        self._ble.gap_disconnect(self._conn_h)
        self._ble.active(False )

def main():
    ble = BleClient(le_secure=True, mitm=False)           # ESP32发起配对时，不支持认证
    if not ble.found_device():  return
    try:
        while True:        
            status,data=ble.read()                        # 读取温度属性并返回状态和读取值
            if status==0:                                 # 成功读取
                print(f'读取结果 {struct.unpack('<h',data)[0]/100 if data else None}℃')
                time.sleep(5)
            elif status==271 or status==261: # 读取的属性标志设为加密读或认证读，status=271/261
                ble.pair()                   # 需要配对，但不能在事件处理中调用pair()
            else:
                print('status:',status)
                ble.deinit(); return
    except KeyboardInterrupt: ble.deinit()
if __name__ == '__main__': main()
