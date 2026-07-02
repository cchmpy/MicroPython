import struct,time
from bluetooth import BLE,UUID
from micropython import const
_IRQ_SCAN_RESULT  = const(5)  # 事件：扫描到一个广播数据包或响应包
_IRQ_SCAN_DONE    = const(6)  # 事件：扫描持续时间已用完或手动停止
_SCAN_RSP         = const(4)  # 广播包类型：扫描响应
# 用于打印输出
_ADDR_TYPE = ('PUBLIC','RANDOM')
_ADDV_TYPE = ('可连接非定向广播','可连接定向广播', '可扫描非定向广播',
              '不可连接非定向广播','扫描响应')
_ADDV_FLAG = ('有限可发现模式','通用可发现模式','不支持BR/EDR',
              '控制器同时支持LE和BR/EDR','主机同时支持LE和BR/EDR')
_UUID_LENGTH  = (0,2,4,16)    # 不同类uuid的字节长度，用于解析


class BleScan:                                        # 类BleScan, 用于扫描、打印BLE设备信息
    def __init__(self,duration_ms=5000, interval_us=500_000, window_us=200_000):
        self._ble = BLE(); self._ble.active(True)
        self._ble.irq(self._irq) 
        self._devices={}                               # 保存扫描的设备信息 
        self._addr = None;  self._addr_type=None       # 保存每次扫描的结果
        self._adv_type = None; self._adv_data = None 
        self._rssi = None
        self._done = False                             # 是否完成扫描和打印 
        print(f'开始扫描，将持续{duration_ms/1000}秒...')
        self._ble.gap_scan(duration_ms,interval_us, window_us, True) 
        
    def _irq(self,event, data):       
        if event==_IRQ_SCAN_RESULT: self._update(data) # 使用data更新设备信息
        elif event == _IRQ_SCAN_DONE:  
            self._print(); self._done = True           # 扫描完成，打印并更新状态

    def _update(self,data):                            # 用数据包更新设备信息
        # 解析数据包内容，每个设备保存的信息是:
        # addr:[0rssi,1addr_type,2adv_type, 3flag, 4name, 5tx_p,
        #      6[UUID], 7[manufacturer], 8广播包数量, 9扫描响应包数量] 
        self._addr_type, self._addr, self._adv_type, self._rssi, self._adv_data = data
        #if self._rssi<-70: return                     # 可过滤部分设备
        addr = bytes(self._addr)                       # 将memoryview类型转换为bytes
        if addr not in self._devices:                  # 若不存在即扫描到新设备，则添加
            self._devices[addr]=[self._rssi,self._addr_type,self._adv_type,
                                 None,None,None,[],None,1,0]
        else:
            self._devices[addr][0]=self._rssi          # 更新接收功率rssi
            if self._adv_type == _SCAN_RSP:            # 若是扫描响应数据包
                self._devices[addr][9]+=1              # 更新扫描响应数据包个数
                if self._devices[addr][9]>1: return    # 同一设备响应包只解析1次
            else:
                self._devices[addr][8]+=1              # 更新广播包个数
                return
        # 解析数据包内容 
        i = 0                                          # i指向数据包的首个字节
        while i+1 < len(self._adv_data):               # adv_data[i+1]是AD_Type
            data=bytes(self._adv_data[i+2:i+self._adv_data[i]+1]) # 截取AD_Data
            AD_Type = self._adv_data[i+1]
            if AD_Type == 0x01:                        # AD_Type为标识flag
                self._devices[addr][3]=data                
            elif AD_Type == 0x08 or AD_Type == 0x09:   # AD_Type为本地名称
                self._devices[addr][4]=data.decode()
            elif AD_Type == 0x0A:                      # AD_Type为发射功率
                self._devices[addr][5]=data 
            elif AD_Type in (2,3,4,5,6,7):             # AD_Type为服务列表                 
                step =_UUID_LENGTH[AD_Type//2]         # uuid对应的字节长度
                for b in range(0,len(data),step):
                    self._devices[addr][6].append(UUID(data[b:b+step])) 
            elif AD_Type == 0xFF:                      # AD_Type为制造商数据
                self._devices[addr][7]=(struct.unpack('<H',data[0:2])[0],data[2:]) 
            i+=self._adv_data[i]+1 
        
    def _print(self):                                  # 按接收功率的递减顺序打印所有设备的信息
        if  (_len :=len(self._devices))==0:
            print('没有扫描到低功耗蓝牙设备。'); return
        r = sorted(self._devices.items(),key=lambda x:x[1][0], reverse=True) # 按rssi递减排序
        for i,d in enumerate(r): 
            print(f'--------------------------------------------(第{i+1}个，共{_len}个)')
            print(f'广播名称：{d[1][4]}')
            print(f'设备地址: {d[0]}')
            print(f'发射功率：{None if d[1][5] is None else d[1][5][0]}')
            print(f'接收功率: {d[1][0]}dBm')
            print(f'地址类型: {_ADDR_TYPE[d[1][1]]}')
            print(f'广播类型: {_ADDV_TYPE[d[1][2]]}')
            print('广播标识：',end='') 
            if d[1][3] is None: print('None')
            else:
                for j in range(5):
                    if (d[1][3][0]>>j) & 0x01:print(_ADDV_FLAG[j],end='|') 
                print('')  
            print(f'服务UUID：{d[1][6]}') 
            print(f'厂商ID和数据:{(hex(d[1][7][0]),d[1][7][1]) if d[1][7] is not None else None}')
            print(f'广播包数量：{d[1][8]}')
            print(f'响应包数量：{d[1][9]}')    
    def wait(self):
        while not self._done: time.sleep_ms(100)
        self._ble.active(False)
if __name__=='__main__':
    ble = BleScan(); ble.wait()                       # 等待扫描完成后，退出程序
