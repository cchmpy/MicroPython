import time,struct,bluetooth as BT
from micropython import const
from ble_advertising import advertising_payload       # 导入程序13-2.py（ble_advertising.py）

_IRQ_CENTRAL_CONNECT    = const(1)  
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE        = const(3)

_fuuid = lambda u128,u16: f'{u128[:4]}{u16}{u128[8:]}'            # 根据基本uuid定义新uuid字符串
_BASE_UUID = '6E400000-B5A3-F393-E0A9-E50E24DCCA9E'
_SRV_UART_UUID = BT.UUID(_fuuid(_BASE_UUID,'0001'))               # 服务uuid
_CHAR_RX = (BT.UUID(_fuuid(_BASE_UUID,'0002')),BT.FLAG_WRITE,)    # RX特性元组
_CHAR_TX = (BT.UUID(_fuuid(_BASE_UUID,'0003')),BT.FLAG_NOTIFY,)   # TX特性元组
_SERVICE_UART = (_SRV_UART_UUID,(_CHAR_RX,_CHAR_TX))              # UART服务元组

class BleUART():
    def __init__(self, name='esp32_UART', rxbuf=100):
        self._name = name
        self._ble=BT.BLE();   self._ble.active(True)
        self._ble.irq(self._irq)  
        ((self._rx_h,self._tx_h),) = self._ble.gatts_register_services((_SERVICE_UART,))
        self._ble.gatts_set_buffer(self._rx_h, rxbuf, True) 
        self._conns = set()                                      # 集合变量，保存所有的连接句柄
        self._rx_buffer = bytearray()                            # 缓存接收的数据

        self._adv_data,self._resp_data = advertising_payload(
            name=self._name, services=[_SRV_UART_UUID],) 
        self._interval_us = 200_000                              # 广播间隔时间
        self._ble.gap_advertise(self._interval_us, self._adv_data, resp_data=self._resp_data)
        print(f'{self._name} BLE服务器已开启广播...')
   
    def _irq(self, event, data): 
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data 
            self._conns.add(conn_handle)            
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle in self._conns:
                self._conns.remove(conn_handle)
            self._ble.gap_advertise(self._interval_us)              # 重启广播
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if conn_handle in self._conns and value_handle == self._rx_h:
                self._rx_buffer.extend(self._ble.gatts_read(self._rx_h)) # 将收到数据附加到缓存末尾
    
    def write(self,data): 
        for conn_h in self._conns:
            self._ble.gatts_notify(conn_h, self._tx_h, data) 
    
    def any_data(self):
        return len(self._rx_buffer)
    
    def read(self, size=None):
        if not size: size = len(self._rx_buffer)
        result = self._rx_buffer[0:size]
        self._rx_buffer = self._rx_buffer[size:]
        return result
    
    def deinit(self):
        for conn_h in self._conns: self._ble.gap_disconnect(conn_h)
        self._conns.clear()
        self._ble.active(False)
    
if __name__ == '__main__':
    ble = BleUART();   i=1
    try:
        while True:
            ble.write(str(i)+'\n')
            if ble.any_data(): print(ble.read())
            i+=1
            time.sleep(1)
    except KeyboardInterrupt: ble.deinit()
