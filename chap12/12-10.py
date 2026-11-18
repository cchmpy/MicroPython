import time,struct,random
from bluetooth import BLE,UUID
from micropython import const
from ble_advertising import decode_name        # 导入程序13-2.py（ble_advertising.py）
_IRQ_SCAN_RESULT                = const(5) 
_IRQ_SCAN_DONE                  = const(6)
_IRQ_PERIPHERAL_CONNECT          = const(7)
_IRQ_GATTC_SERVICE_RESULT        = const(9)
_IRQ_GATTC_SERVICE_DONE          = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_NOTIFY                = const(18)
_IRQ_MTU_EXCHANGED               = const(21)
_SRV_UART_UUID = UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_CHAR_RX_UUID = UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")  # WRITE
_CHAR_TX_UUID = UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")  # NOTIFY
class BleUARTClient():    
    def __init__(self, srv_name='esp32_UART'): 
        self._srv_name = srv_name                            # 待连接服务器的名字
        self._ble = BLE(); self._ble.active(True)
        self._ble.irq(self._irq)
        self._found = False 
        self._conn_h = None                                  # 与服务器的连接句柄
        self._notify_cb = None                               # 通知回调函数，处理通过通知接收的数据
        self._start,self._end = None,None                    # uart服务的开始和结束句柄
        self._rx_value,self._tx_value = None, None           # 特性值句柄
        self._ble.gap_scan(3000,500_000, 200_000, True)      # 开始扫描
    def _irq(self,event, data):
        # ---------------------------------------------------扫描
        if event == _IRQ_SCAN_RESULT: 
            addr_type, addr, _, _, adv_data = data 
            if decode_name(bytes(adv_data))==self._srv_name:         # 找到设备
                self._found = True
                self._ble.gap_connect(addr_type, addr)        # 发起连接
        elif event == _IRQ_SCAN_DONE: 
            if not self._found: print(f'没有发现设备{self._srv_name}。')
     # ---------------------------------------------------连接和mtu交换 
        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            self._conn_h = conn_handle
            self._ble.gattc_exchange_mtu(self._conn_h)        # mtu交换
        elif event == _IRQ_MTU_EXCHANGED:
            conn_handle, mtu = data 
            self._ble.gattc_discover_services(self._conn_h,_SRV_UART_UUID) # 搜索UART服务
        # ----------------------------------------------------搜索服务
        elif event == _IRQ_GATTC_SERVICE_RESULT: 
            conn_handle, start_handle, end_handle, uuid = data 
            if conn_handle == self._conn_h and uuid == _SRV_UART_UUID:
                self._start, self._end = start_handle, end_handle
        elif event == _IRQ_GATTC_SERVICE_DONE: 
            if self._start and self._end:                    # 搜索特性
                self._ble.gattc_discover_characteristics( self._conn_h, self._start, self._end)
            else:   print('没有发现UART服务。')
        # ---------------------------------------------------搜索特性
        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT: 
            conn_handle, end_handle, value_handle, properties, uuid = data
            if conn_handle == self._conn_h:
                if uuid==_CHAR_RX_UUID:  self._rx_value = value_handle
                elif uuid == _CHAR_TX_UUID:  self._tx_value = value_handle
        # ---------------------------------------------------通知
        elif event == _IRQ_GATTC_NOTIFY:
            conn_handle, value_handle, notify_data = data
            if self._notify_cb is not None:
                self._notify_cb(bytes(notify_data))          # 调用回调函数 
    def callback(self,cb): self._notify_cb = cb
    def write(self,data,mode=0):
        if self._rx_value is not None:
            self._ble.gattc_write(self._conn_h,self._rx_value,data,mode)
            return True
        else:  return False
    def deinit(self): self._ble.active(False)
def main():
    ble = BleUARTClient('esp32_UART') 
    cb = lambda x:print('接收:',x.decode()) 
    ble.callback(cb)
    try:
        while True:
            s = str(random.randint(1,99999)) 
            if ble.write(s):  print('写入：',s)
            time.sleep(1)
    except KeyboardInterrupt: ble.deinit()
if __name__ == '__main__': main()
