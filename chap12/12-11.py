import json
from bluetooth import BLE
from micropython import const, schedule
_IRQ_GET_SECRET      = const(29)               # 事件：配对开始时密钥列表请求
_IRQ_PASSKEY_ACTION  = const(31)               # 事件：认证时密钥请求动作
_IRQ_SET_SECRET      = const(30)               # 事件：配对末期密钥分发
_IRQ_ENCRYPTION_UPDATE = const(28)             # 事件：加密状态已更新
# _IRQ_PASSKEY_ACTION事件中action可用值
_PASSKEY_ACTION_INPUT = const(2)
_PASSKEY_ACTION_DISP  = const(3)
_PASSKEY_ACTION_NUMCMP = const(4)
_ACTION_TXT =(None,None,'_PASSKEY_ACTION_INPUT','_PASSKEY_ACTION_DISP','_PASSKEY_ACTION_NUMCMP') # 打印用

class BleSec:
    def __init__(self, path='ble_secrets.json'):
        self._ble       = BLE()
        self._file      = path                 # 保存密钥的文件
        self._secrets   = {}                   # 保存密钥的字典
        self._modified  = False                # 密钥是否被修改，以决定是否保存到文件
        self._encrypted = False                # 连接是否被加密，用于判断配对是否完成
        self._cnt_get   = 0                    # _IRQ_GET_SECRET事件触发次数，打印用
        self._cnt_set   = 0                    # _IRQ_SET_SECRET事件触发次数，打印用

    def _save_secrets(self,_):                 # 把密钥从字典保存到文件,伪参数'-'避免schedule传参错误
        if not self._modified: return          # 密钥未修改，不保存
        try:
            with open(self._file, 'w') as f:               
                json_secrets = [(sec_type, key.hex(), value.hex())
                                for (sec_type, key), value in self._secrets.items()]
                json.dump(json_secrets, f)      # 转换为JSON字符串保存
                self._modified = False
                print('密钥保存成功！')
        except: print("密钥保存失败！") 

    def _load_secrets(self):                    # 把密钥从文件载入到字典
        try:
            with open(self._file, 'r') as f:
                entries = json.load(f)
                for sec_type, key, value in entries:
                    self._secrets[sec_type, bytes.fromhex(key)] = bytes.fromhex(value)
                print('从文件载入密钥成功！')
        except: print("没有可用密钥")

    def _security_irq(self, event, data):       # 安全事件回调函数
        if event == _IRQ_ENCRYPTION_UPDATE:     # 加密状态已更新
            conn_handle, encrypted, authenticated, bonded, key_size = data
            self._encrypted = encrypted
            print('触发事件:_IRQ_ENCRYPTION_UPDATE', f'encrypted:{encrypted}, authenticated:{authenticated}, bonded:{bonded}, key_size:{key_size}')  
        elif event == _IRQ_GET_SECRET:          # 配对开始时请求密钥列表，需要返回一个已存储的密钥
            sec_type, index, key = data
            self._cnt_get+=1                    # 事件计数器
            print(f'触发事件:_IRQ_GET_SECRET {self._cnt_get}次', f'sec_type:{sec_type}, index:{index}, key:{bytes(key) if key else None}')
            if key is None:
                i = 0
                for (t, _key), value in self._secrets.items():
                    if t == sec_type:
                        if i == index: return value  # 返回sec_type的第一个索引值
                        i += 1
                return None                     # 没有就返回none
            else:
                key = sec_type, bytes(key)      # 如果key索引存在，直接用它取密钥
                return self._secrets.get(key, None) 
        elif event == _IRQ_PASSKEY_ACTION:      # 在配对认证时响应密钥请求,根据不同action，交换密钥
            conn_handle, action, pkey = data
            print('触发事件:_IRQ_PASSKEY_ACTION',f'action:{_ACTION_TXT[action]} pkey:{pkey}')
            if action == _PASSKEY_ACTION_NUMCMP:
                print(f'passkey={pkey}')
                accept = int(input("比较数字是否相同? 相同输入1，否则输入0:"))  
                self._ble.gap_passkey(conn_handle, action, accept) 
            elif action == _PASSKEY_ACTION_DISP:
                passkey=random.randint(0,999999)
                print(f'请在对端设备输入配对密钥:{passkey:06d}') 
                self._ble.gap_passkey(conn_handle, action, passkey)
            elif action == _PASSKEY_ACTION_INPUT: 
                passkey = int(input('请输入对端设备显示的密钥:'))
                self._ble.gap_passkey(conn_handle,action, passkey) 
            else: print("unknown action")
        elif event == _IRQ_SET_SECRET:          # 分配密钥，将其保存到字典，需要返回True或False
            sec_type, key, value = data
            key = sec_type, bytes(key)
            value = bytes(value) if value else None
            self._cnt_set+=1
            print(f"触发事件:_IRQ_SET_SECRET {self._cnt_set}次 ", f'sec_type:{sec_type},key:{key}, value:{value}')
            if value is None: 
                if key in self._secrets:
                    del self._secrets[key]
                    return True
                else: return False
            else: self._secrets[key] = value
            self._modified = True               # 密钥被修改
            schedule(self._save_secrets,None)   # 排队保存(不同步写入flash)
            return True 
        else: print('event:',event)             # 其它事件，打印事件的ID