import time,struct
from bluetooth import BLE,UUID
from micropython import const
from ble_advertising import decode_name        # 导入程序13-2.py（ble_advertising.py）
_IRQ_SCAN_RESULT                 = const(5) 
_IRQ_SCAN_DONE                   = const(6)
_IRQ_PERIPHERAL_CONNECT          = const(7)
_IRQ_GATTC_SERVICE_RESULT        = const(9)
_IRQ_GATTC_SERVICE_DONE          = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_NOTIFY                = const(18)
_SRV_ENV_UUID  = UUID(0x181A)
_TEMP_UUID    = UUID(0x2A6E)
_HUM_UUID      = UUID(0x2A6F)

class BleEnvClient(): 
    def __init__(self, srv_name='esp32_temp'): 
        self._srv_name = srv_name                           # 待连接的服务器名字
        self._ble = BLE(); self._ble.active(True)
        self._ble.irq(self._irq)
        self._found = False 
        self._conn_h = None                                  # 与服务器的连接句柄 
        self._start,self._end = None,None                    # 环境感应服务的开始和结束句柄
        self._temp_notify_cb,self._hum_notify_cb = None,None # 温湿度特性回调函数
        self._temp_value,self._hum_value = None, None        # 温湿度特性值句柄
        self._ble.gap_scan(3000,500_000, 200_000, True)      # 开始扫描
    def _irq(self,event, data):
        # ---------------------------------------------------扫描
        if event == _IRQ_SCAN_RESULT: 
            addr_type, addr, _, _, adv_data = data 
            if decode_name(bytes(adv_data))==self._srv_name: # 找到设备
                self._found = True
                self._ble.gap_connect(addr_type, addr)       # 发起连接
        elif event == _IRQ_SCAN_DONE: 
            if not self._found: print(f'没有发现设备{self._srv_name}。')
        # ---------------------------------------------------连接 
        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            self._conn_h = conn_handle
            self._ble.gattc_discover_services(self._conn_h,_SRV_ENV_UUID) # 开始搜索环境感应服务
        # ---------------------------------------------------搜索服务
        elif event == _IRQ_GATTC_SERVICE_RESULT: 
            conn_handle, start_handle, end_handle, uuid = data
            if uuid == _SRV_ENV_UUID: self._start, self._end = start_handle, end_handle
        elif event == _IRQ_GATTC_SERVICE_DONE: 
            if self._start and self._end:                    # 开始搜索特性
                self._ble.gattc_discover_characteristics( self._conn_h, self._start, self._end)
            else: print('没有发现环境感应服务。') 
        # ---------------------------------------------------搜索特性
        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            conn_handle, end_handle, value_handle, properties, uuid = data
            if uuid==_TEMP_UUID: self._temp_value = value_handle
            elif uuid == _HUM_UUID: self._hum_value = value_handle 
        # ---------------------------------------------------通知
        elif event == _IRQ_GATTC_NOTIFY:            
            conn_handle, value_handle, notify_data = data
            if self._temp_notify_cb is not None and value_handle==self._temp_value:
                self._temp_notify_cb(notify_data)
            if self._hum_notify_cb is not None and value_handle==self._hum_value:
                self._hum_notify_cb(notify_data) 
    def callback(self,temp_cb,hum_cb):
        self._temp_notify_cb = temp_cb
        self._hum_notify_cb = hum_cb
    def deinit(self): self._ble.active(False)

def main():
    ble = BleEnvClient('esp32_temp')
    handle = lambda x:struct.unpack('<h',x)[0]/100
    temp_h = lambda x:print(f'温度：{handle(x)}℃')
    hum_h  = lambda x:print(f'湿度：{handle(x)}%')
    ble.callback(temp_h,hum_h)                                # 设置温湿度特性数据处理回调函数
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: ble.deinit()
if __name__ == '__main__':  main()
