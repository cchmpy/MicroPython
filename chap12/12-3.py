from bluetooth import BLE, UUID
from micropython import const
from ble_advertising import advertising_payload   # 导入程序13-2.py（ble_advertising.py）
_IRQ_CENTRAL_CONNECT    = const(1)                # 中央设备（客户端）连接事件
_IRQ_CENTRAL_DISCONNECT = const(2)                # 中央设备（客户端）断连事件
_ENV_SENSE_UUID         = UUID(0x181A)            # 环境传感服务uuid
_ADV_APPEARANCE         = 0x0300                  # 一般温度计外观

class BleTemp():
    def __init__(self,name='esp32_temp'):
        self._name = name
        self._ble  = BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._adv_data,self._resp_data = advertising_payload(
            name=self._name, services=[_ENV_SENSE_UUID], appearance=_ADV_APPEARANCE,
            manufacturer=[0xF000,'ESP32 TEMP'.encode()])       
        
        self._interval_us = 200_000                # 广播间隔时间 
        self._ble.gap_advertise(self._interval_us, self._adv_data, resp_data=self._resp_data)
        print(f'{self._name}蓝牙服务器已开启广播...')
        
    def _irq(self, event, data):                   # 事件处理回调函数 
        if event == _IRQ_CENTRAL_CONNECT: 
            print('触发事件:_IRQ_CENTRAL_CONNECT','一个中央设备与此外围设备建立连接！')
        elif event == _IRQ_CENTRAL_DISCONNECT: 
            print('触发事件:_IRQ_CENTRAL_DISCONNECT',f'连接已断开，{self._name}重启广播...') 
            self._ble.gap_advertise(self._interval_us)
            
    def deinit(self):                              # 关闭射频模块
        self._ble.active(False)

def main():
    import time    
    try:
        ble_temp = BleTemp()
        while  True:  time.sleep(1)
    except (KeyboardInterrupt,ValueError) as e:
        ble_temp.deinit(); print(e)

if __name__ == '__main__': main()