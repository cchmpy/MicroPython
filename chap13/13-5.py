from bluetooth import BLE
from micropython import const
from ble_advertising import decode_name  # 导入程序13-2.py（ble_advertising.py）
_IRQ_SCAN_RESULT           = const(5)    # 扫描到一个广播数据包或响应包
_IRQ_SCAN_DONE             = const(6)    # 扫描持续时间已用完或手动停止
_IRQ_PERIPHERAL_CONNECT    = const(7)    # 本地中央设备连接到一个外围设备
_IRQ_PERIPHERAL_DISCONNECT = const(8)    # 本地中央设备与一个外围设备断开连接

class BleClient(): 
    def __init__(self, srv_name='esp32_temp'): 
        self._srv_name = srv_name                                  # 待连接服务器的名字 
        self._ble = BLE();  self._ble.active(True)
        self._ble.irq(self._irq) 
        self._conn_h = None                                        # 与服务器的连接句柄
        self._addr_type = None; self._addr = None                  # 服务器广播地址类型和地址
        self._ble.gap_scan(5000,500_000, 200_000, True)            # 启动扫描
        
    def _irq(self,event, data): 
        if event == _IRQ_SCAN_RESULT: 
            addr_type, addr, _, _, adv_data = data
            if decode_name(bytes(adv_data))==self._srv_name:        # 找到设备 
                self._addr_type=addr_type; self._addr=bytes(addr)   # 保存目标地址数据
                self._ble.gap_scan(None)                            # 停止扫描  
        elif event == _IRQ_SCAN_DONE:            
            if self._addr_type is None  and self._addr is None:
                print(f'没有发现{self._srv_name}设备。')
            else:
                self._ble.gap_connect(self._addr_type,self._addr)   # 发起连接
        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            if addr_type == self._addr_type and addr == self._addr:
                self._conn_h = conn_handle
                print(f'已连接到{self._srv_name}设备。')
        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle == self._conn_h: self._conn_h=None 
    
    def is_connected(self):
        return self._conn_h is not None
    
    def disconnect(self):
        if self.is_connected():
            self._ble.gap_disconnect(self._conn_h)
            while self.is_connected(): time.sleep_ms(10)            # 等待断开连接
            print('已断开连接。')
            self._ble.active(False)                                 # 关闭无线电
    
if __name__ == '__main__':
    import time
    ble = BleClient()
    try:
        while not ble.is_connected(): time.sleep_ms(100)
        print('3秒后退出...')
        time.sleep(3); ble.disconnect()
    except KeyboardInterrupt: pass
    
