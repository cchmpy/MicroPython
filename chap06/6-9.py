import json, time
from network import WLAN
from esp32 import NVS

class WifiNvsManager:
    def __init__(self, name_space='wifi_store', blob_key='wifi_cred', len_key='wifi_cred_len'):
        self._nvs = NVS(name_space)                             # 创建NVS对象
        self._blob_key = blob_key                               # 保存Wi-Fi账户的键
        self._len_key = len_key                                 # 存储blob字节长度的键
        self._wifi_cred = self._load()                          # 载入所有账户信息,结果是字典对象
    
    def _load(self):                                            # 载入所有账户数据，反序列化为字典
        try: 
            blob_len = self._nvs.get_i32(self._len_key)         # 先读取blob数据的字节长度
            if blob_len <= 0: 
                raise ValueError('Invalid blob length')
            buf = bytearray(blob_len)                           # 定义保存blob的bytearray
            self._nvs.get_blob(self._blob_key, buf)             # 读取blob数据
            return json.loads(buf.decode())                     # 反序列化为字典,可能抛出ValueError 
        except (OSError,ValueError) as err: 
            return {'accounts': {},'last_valid': (None,None) }  # 首次读取或数据错误，返回空结构
        
    def _save(self, blob_data:bytes):                           # 内部方法：存储blob数据和其字节长度
        nvs = self._nvs
        try:                                                    # 先删原数据,避免长度不匹配或blob残留
            nvs.erase_key(self._blob_key)
            nvs.erase_key(self._len_key)
        except OSError:  pass                                   # 首次存储无数据，忽略删除失败错误 
        nvs.set_blob(self._blob_key, blob_data)                 # 存储blob数据(json序列化后的bytes)
        nvs.set_i32(self._len_key, len(blob_data))              # 存储blob数据的字节长度
        nvs.commit()                                            # 提交保存
        
    def get_last_valid(self):                                   # 返回最近有效的ssid和key 
        return self._wifi_cred.get('last_valid',(None,None))
    
    def get_all(self):                                          # 返回所有账号信息
        return self._wifi_cred.get('accounts',{})
    
    def save_ssid_key(self, ssid:str, key:str, last_valid=False,**kwargs): 
        # 保存单个账户信息,kwargs是该账户额外信息(字典类型)
        wifi_c = self._wifi_cred                                # 所有账户的字典对象        
        key_data = wifi_c['accounts'].get(ssid,None)            # 获取ssid对应的key数据(列表）
        if key_data:                                            # 存在同名账户
            same_key = False                                    # 密码是否相同
            for d in key_data:                                  # 遍历列表,其内每个元素是dict
                if d['key'] == key:                             # 密码相同(更新账号信息) 
                    for k,v in kwargs.items(): d[k]=v           # 更新或添加额外信息
                    same_key = True
                    break
            if not same_key:                                    # 密码不同
                new_key = {'key':key}                           # 添加密码信息
                for k,v in kwargs.items(): new_key[k]=v         # 添加额外信息
                key_data.append(new_key)                        # 列表增加一个字典元素                             
        else:                              # 新账户如："C7LHU": [{"key": "1234", "rssi": -37,… }]
            key_data = {}
            key_data['key'] = key                               # 添加密码信息
            for k,v in kwargs.items(): key_data[k] = v          # 添加额外信息 
            wifi_c['accounts'][ssid] = [key_data,]              # 添加该账户完整信息
        
        if last_valid:                                          # 设为最近有效账号
            wifi_c['last_valid'] =(ssid,key) 
        self._save(json.dumps(wifi_c).encode())                 # 保存所有账户信息
        
    def connect_wifi(self, timeout=15):       # 使用NVS保存的ssid和key连接互联网，timeout是超时秒数        
        def _connect(ssid,key):                                 # 嵌套函数：连接Wi-Fi
            nonlocal sta, timeout
            t = timeout
            try:
                if not sta.isconnected():
                    print(f'连接到{ssid}...')
                    sta.connect(ssid, key)
                    while not sta.isconnected() and t>0:        # 如果没有连接且不超时
                        time.sleep(1);  t -= 1
            except OSError as err: pass 
            if not sta.isconnected(): sta.disconnect()          # 若连接失败,断开之前的连接尝试
            return sta.isconnected()                            # 返回连接状态
        
        sta = WLAN(WLAN.IF_STA)                                 # 创建STA接口对象
        sta.active(True)                                        # 开启射频模块
        scans = [x[0].decode() for x in sta.scan()]             # 扫描当前环境的wi-fi热点,创建包含ssid的列表
        
        # 1. 连接最近有效热点-----------------------------
        ssid_v, key_v = self.get_last_valid()                   # 有效热点账号 
        if ssid_v and key_v and (ssid_v in scans):              # 当前环境有和“最近有效账号”同名的热点
            if _connect(ssid_v, key_v):
                print('连网成功：',sta.ifconfig())               # 打印IP地址信息
                return sta                                      # 如果已成功连网，返回sta对象        
        # 2. 若连接失败，则尝试连接其它热点---------------        
        saves = self.get_all()                                  # 获取NVS保存的所有热点信息
        if len(saves)==0 or len(scans)==0:
            print('连网失败，nvs中没有热点信息')
            return False                                        # 连网失败,返回False
        for ssid in scans:                                      # 从最强信号的热点逐个尝试            
            keys = saves.get(ssid,None)                         # 从nvs获取热点对应的keys
            if keys: 
                for k in keys:
                    key = k['key']
                    if ssid!=ssid_v and key!=key_v:             # 避免重复连接
                        if _connect(ssid, key):
                            print('连网成功：',sta.ifconfig())
                            self.save_ssid_key(ssid,key,True)   # 更新最近有效热点信息
                            return sta                          # 如果已成功连网，返回sta对象
        print('连网失败，已尝试了nvs保存的所有热点信息')
        return False                                            # 连网失败,返回False

if __name__ == '__main__':
    wifi_mg = WifiNvsManager()
    print(f'{wifi_mg.get_all()}\n{wifi_mg.get_last_valid()}')   # 打印NVS保存的热点信息
    if not (sta:=wifi_mg.connect_wifi()):                       # 如果连网失败
        ssid, key = 'my_ssid','my_key'                          # 模拟配网操作获取的热点信息
        wifi_mg.save_ssid_key(ssid, key, True)                  # 添加账号,并设为最近有效热点
        sta = wifi_mg.connect_wifi()                            # 连接Wi-Fi
        print(f'{wifi_mg.get_all()}\n{wifi_mg.get_last_valid()}')
    if sta:                                                     # 断开连接,关闭射频 
        sta.disconnect()
        sta.active(False)
