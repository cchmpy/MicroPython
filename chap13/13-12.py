import time,struct,random,bluetooth as BT
from bluetooth import UUID
from micropython import const
from blesec import BleSec                              # 导入程序13-11.py（blesec.py）
from ble_advertising import advertising_payload        # 导入程序13-2.py（ble_advertising.py）
# 事件ID
_IRQ_CENTRAL_CONNECT            = const(1)
_IRQ_CENTRAL_DISCONNECT         = const(2)
_IRQ_CONNECTION_UPDATE         = const(27)

_IO_CAPABILITY_KEYBOARD_DISPLAY = const(4)                    # 设备I/O能力
_FLAG_READ_ENCRYPTED            = const(0x0200)               # 属性的安全性标志:加密读
# 服务
_SRV_ENV_UUID = UUID(0x181A)
_DESC    = (UUID(0x2901),BT.FLAG_READ)                        # 描述符元组
_CHAR_TEMP = (UUID(0x2A6E),BT.FLAG_READ | _FLAG_READ_ENCRYPTED, (_DESC,))    # 温度特性元组
_SERV_ENV  = (_SRV_ENV_UUID,(_CHAR_TEMP,))                    # 环境感应服务元组
_SERV = (_SERV_ENV, )                                         # 待注册的服务元组

class BleTemp(BleSec):
    def __init__(self,*,json_file='secrets_srv.json',name='esp32_temp',le_secure=True,mitm=True):
        super().__init__(json_file)                          # 先初始化父类
        self._name = name                                    # 设备名称，广播名称
        self._load_secrets()                                 # 把保存在文件的密钥载入到字典
        self._ble.irq(self._irq)       
        self._ble.active(True)                               # 先设回调，在打开无线射频        
        self._ble.config(bond=True,le_secure=le_secure,mitm=mitm,io=_IO_CAPABILITY_KEYBOARD_DISPLAY)
        self._ble.config(gap_name=self._name, addr_mode=2)   # 使用可解析的私有地址 
        
        ((self._temp_h,self._temp_desc_h),) = self._ble.gatts_register_services(_SERV) 
        self._ble.gatts_write(self._temp_desc_h,'客厅温度'.encode()) # 初始化描述符值
        self._conn_h = set()                                 # 定义集合变量，保存所有的连接句柄
        
        self._cnt_conn_upd = 0                   # CONNECTION_UPDATE事件被触发次数,用于打印信息
        self._interval_us = 100_000               # 广播间隔时间
        self._adv_data,self._rsp_data = advertising_payload(name=self._name,
                                                            services=[_SRV_ENV_UUID]) 
        self._ble.gap_advertise(self._interval_us, self._adv_data, resp_data=self._rsp_data)
        print(f'{self._name} BLE服务器已开启广播...')       

    def _irq(self, event, data):                  # 事件处理回调函数
        if event == _IRQ_CENTRAL_CONNECT:         # 中央设备(客户端)与此外围设备(服务器)建立连接
            conn_handle, _, _ = data
            self._conn_h.add(conn_handle)
            print('触发事件:_IRQ_CENTRAL_CONNECT','一个中央设备与此外围设备建立连接！')
            # 重置成员变量
            self._modified, self._encrypted = False, False
            self._cnt_get,self._cnt_set,self._cnt_conn_upd = 0,0,0  
        elif event == _IRQ_CENTRAL_DISCONNECT:    # 中央设备(客户端)与此外围设备(服务器)断开连接
            conn_handle, _, _ = data
            self._conn_h.discard(conn_handle)
            print('触发事件:_IRQ_CENTRAL_DISCONNECT',f'一个中央设备与此外围设备断开连接，{self._name}重启广播...') 
            self._ble.gap_advertise(self._interval_us)
        elif event == _IRQ_CONNECTION_UPDATE:     # 远端设备更新连接参数
            conn_handle, conn_interval, conn_latency, supervision_timeout, status = data 
            self._cnt_conn_upd +=1
            print(f'触发事件:_IRQ_CONNECTION_UPDATE {self._cnt_conn_upd}次','远端设备更新连接参数')
        else:
            try:                                           # 取消配对时，需要进行异常处理
                return self._security_irq(event, data)     # 安全事件处理回调函数
            except OSError:
                for c in self._conn_h: self._ble.gap_disconnect(c)

    def set_temp(self):                           # 测量并更新特性值，此处用随机数模拟测量过程
        self._ble.gatts_write(self._temp_h, struct.pack('<h',random.randint(2000,3000)))
    def deinit(self): self._ble.active(False)

def main():
    ble = BleTemp(le_secure=True, mitm= True)
    try:
        while True:  ble.set_temp(); time.sleep(1)
    except KeyboardInterrupt: ble.deinit()
if __name__ == '__main__':  main()
