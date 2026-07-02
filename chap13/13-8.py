import time
from bluetooth import BLE,UUID
from micropython import const
from ble_advertising import decode_name      # 导入程序13-2.py（ble_advertising.py）
_IRQ_SCAN_RESULT                 = const(5)   
_IRQ_SCAN_DONE                   = const(6)
_IRQ_PERIPHERAL_CONNECT          = const(7)
_IRQ_PERIPHERAL_DISCONNECT       = const(8)
_IRQ_GATTC_SERVICE_RESULT        = const(9)
_IRQ_GATTC_SERVICE_DONE          = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE   = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT     = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE       = const(14)
class BleDiscoveServices():
    def __init__(self,srv_name): 
        self._srv_name = srv_name  # 待连接服务器的名字
        self._ble = BLE();  self._ble.active(True)
        self._ble.irq(self._irq)
        self._conn_h   = None     # 与服务器的连接句柄
        self._services = []         # 保存所有服务的句柄
        self._atts = {}         # 保存所有属性的字典 handle:uuid
        self._found = False       # 是否找到设备
        self._done  = False        # 是否完成所有操作
        self._ble.gap_scan(5000,500_000, 200_000, True)
    
    def _irq(self,event, data):
        # ----------------------------------------------------------扫描
        if event == _IRQ_SCAN_RESULT: 
            addr_type, addr, _, _, adv_data = data
            if decode_name(bytes(adv_data))==self._srv_name:   # 找到设备
                self._found = True
                print(f'已经发现设备{self._srv_name},现在连接...')
                self._ble.gap_connect(addr_type, addr)         # 发起连接 
        elif event == _IRQ_SCAN_DONE: 
            if not self._found:
                print(f'没有发现设备{self._srv_name}。')
                self._done = True 
        # ----------------------------------------------------------连接 
        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            self._conn_h = conn_handle
            print(f'已连接到设备{self._srv_name},现在搜索服务...')
            self._ble.gattc_discover_services(self._conn_h) 
        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, _, _ = data
            print('已断开连接。')
            self._conn_h, self._done =None,True 
        # ----------------------------------------------------------搜索服务
        elif event == _IRQ_GATTC_SERVICE_RESULT: 
            conn_handle, start_handle, end_handle, uuid = data
            self._services.append(start_handle)
            self._atts[start_handle]=(UUID(uuid)) 
        elif event == _IRQ_GATTC_SERVICE_DONE: 
            conn_handle, status = data 
            print(f'搜索服务完成,共发现{len(self._atts)}个服务,现在搜索特性...')
            self._ble.gattc_discover_characteristics(self._conn_h,1,0xffff)
        # ----------------------------------------------------------搜索特性
        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            conn_handle, end_handle, value_handle, properties, uuid = data
            self._atts[value_handle]=[(UUID(uuid)),properties]
        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE: 
            conn_handle, status = data
            print('搜索特性完成,现在搜索描述符...')
            self._ble.gattc_discover_descriptors(self._conn_h,1,0xffff)
        # ----------------------------------------------------------搜索描述符
        elif event == _IRQ_GATTC_DESCRIPTOR_RESULT: 
            conn_handle, dsc_handle, uuid = data
            if dsc_handle not in self._atts:
                self._atts[dsc_handle]=(UUID(uuid))
        elif event == _IRQ_GATTC_DESCRIPTOR_DONE:
            conn_handle, status = data
            self._print()
            self._ble.gap_disconnect(self._conn_h)              # 断开连接
    
    def _print(self):
        d = UUID(0x2803)                                        # 特性声明
        r = sorted(self._atts.items(),key=lambda x:x[0])        # 按属性句柄排序
        print('现在打印整体服务框架...')
        for a in r:
            if a[0] in self._services: print(a[0],a[1],'服务')   # 服务
            elif a[1] == d: print('  |---',a[0],a[1],'特性声明')  # 特性声明
            elif type(a[1])==list:                               # 特性
                b = a[1][1]
                print('      |---',a[0],a[1][0],end=' ')
                if b & 1 : print('广播',end=' ')
                if b & 2 : print('读取',end=' ')
                if b & 4 : print('无响应写入',end=' ')
                if b & 8 : print('写入',end=' ')
                if b & 16 : print('通知',end=' ')
                if b & 32 : print('指示',end=' ')
                if b & 64 : print('签名写',end=' ')
                if b & 128 : print('扩展',end='')
                print('')
            else: print('      |---',a[0],a[1]) 
    
    def wait_done(self):
        while not self._done: time.sleep_ms(5)    
    def deinit(self): self._ble.active(False)
    
def main():
    ble = BleDiscoveServices('esp32_temp')
    ble.wait_done()
    ble.deinit()
    
if __name__ == '__main__':  main()
