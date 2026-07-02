import time,struct,dht,bluetooth as BT
from micropython import const
from ble_advertising import advertising_payload       # 导入程序13-2.py（ble_advertising.py）
_IRQ_CENTRAL_CONNECT    = const(1)  
_IRQ_CENTRAL_DISCONNECT = const(2) 
_ADV_APPEARANCE         = const(0x0300)               # 一般温度计外观id
_BLE_MAX_CONNECTIONS    = const(3)                    # 最大连接数

_SRV_ENV_UUID = BT.UUID(0x181A)
_DESC      = (BT.UUID(0x2901),BT.FLAG_READ)                            # 描述符元组
_CHAR_TEMP = (BT.UUID(0x2A6E),BT.FLAG_READ | BT.FLAG_NOTIFY, (_DESC,)) # 温度特性元组
_CHAR_HUM  = (BT.UUID(0x2A6F),BT.FLAG_READ | BT.FLAG_NOTIFY, (_DESC,)) # 湿度特性元组
_SERVICE_ENV = (_SRV_ENV_UUID,(_CHAR_TEMP,_CHAR_HUM))                  # 环境感应服务元组
_SERVICES    = (_SERVICE_ENV,)

class BleTemp():
    def __init__(self, dht_pin=23, name='esp32_temp'):
        self._dht11 = dht.DHT11(dht_pin)                               # 温湿度传感器定义
        self._name = name
        self._ble=BT.BLE();    self._ble.active(True)
        self._ble.irq(self._irq)
        
        ((self._temp_h,self._temp_desc_h,self._hum_h,self._hum_desc_h),) = \
        self._ble.gatts_register_services(_SERVICES)                   # 注册服务
        self._ble.gatts_write(self._temp_desc_h,'客厅温度'.encode())   # 写入描述符值
        self._ble.gatts_write(self._hum_desc_h,'客厅湿度'.encode()) 
        self._conns = set()                                            # 集合，保存所有连接句柄
        self._adv_data,self._resp_data = advertising_payload(
            name=self._name, services=[_SRV_ENV_UUID], appearance=_ADV_APPEARANCE,
            )                                                          # 定义广播负载
        self._interval_us = 200_000                                    # 广播间隔时间
        self._ble.gap_advertise(self._interval_us, self._adv_data, resp_data=self._resp_data)
        print(f'{self._name}低功耗蓝牙服务器已开启广播...')
        
    def _irq(self, event, data): 
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data 
            self._conns.add(conn_handle)
            print(f'当前连接设备：{len(self._conns)}个。')
            if len(self._conns) < _BLE_MAX_CONNECTIONS:                 # 连接数小于最大数
                self._ble.gap_advertise(self._interval_us)              # 重启广播
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._conns.remove(conn_handle)
            print(f'当前连接设备：{len(self._conns)}个。') 
            if len(self._conns)<=_BLE_MAX_CONNECTIONS-1: 
                self._ble.gap_advertise(self._interval_us)              # 重启广播
                
    def set_temp_hum(self, notify=True):                 # 读取传感器，设置特性值并发送通知
        self._dht11.measure()                                           # 测量
        t = self._dht11.temperature()                                   # 读取测量结果
        h = self._dht11.humidity() 
        self._ble.gatts_write(self._temp_h, struct.pack('<h', int(t * 100)))
        self._ble.gatts_write(self._hum_h,  struct.pack('<h', int(h * 100)))
        if notify:
            for c in self._conns:
                self._ble.gatts_notify(c, self._temp_h)
                self._ble.gatts_notify(c,self._hum_h)
    
    def deinit(self):  self._ble.active(False)

if __name__ == '__main__':
    ble = BleTemp()
    try:
        while True:
            ble.set_temp_hum(); time.sleep(5)
    except KeyboardInterrupt:   ble.deinit()
