import network, espnow, hmac, cryptolib, os
class EspnowE2E:
    _instance = None 
    pmk = b'\xd2m,w\xc2\xf4\xd0\xfd\xae\xfd\xa0\x8d\x95;Av' # 预置PMK
    e2e_key = b'4a0l\xb9\xe8:\x18\xbe^x\xe8C}t\x97'         # 预置端到端密码
    
    def __new__(cls,*args,**kwargs):                        # 保证该类只能创建单例对象
        if cls._instance is None:
            cls._instance = super().__new__(cls) 
        return cls._instance
    
    def __init__(self,pmac):
        self.pmac= pmac                                     # 对端mac地址
        self.buf= memoryview(bytearray(250))                # 加密和消息接收共用缓存，长度必须为250
        self.buf_in = [None,self.buf]                       # 用于方法recvinto()的参数,接收数据 
        self.sta = network.WLAN(network.WLAN.IF_STA)
        self.sta.active(True)                               # 打开WLAN端口
        
        mac = self.sta.config('mac')                        # 本设备mac地址
        _lmk = self.pmk + (pmac+mac if pmac<=mac else mac+pmac)         # 辅助生成LMK
        self.lmk = hmac.HMAC(self.e2e_key,_lmk,'sha256').digest()[:16]  # 动态生成LMK 
        
        self.e = espnow.ESPNow()
        self.e.active(True)
        self.e.set_pmk(self.pmk)                            # 设置PMK
        self.e.add_peer(pmac,lmk=self.lmk)                  # 添加对端设备并设置LMK,启用加密通道
     
    def encrypt_e2e(self,msg):                              # HMAC+AES-CTR，加密并生成消息认证码
        size = len(msg)        
        if size>218: msg = msg[:218]                        # 若消息过长则截取，满足218+32=250 
        iv = os.urandom(16)                                 # 设置AES-CTR加密用nonce(iv)
        cipher = cryptolib.aes(self.e2e_key,6,iv)           # 定义AES-CTR模式加密对象
        cipher.encrypt(msg,self.buf)                        # 加密msg至buf 
        hm = hmac.HMAC(self.e2e_key,self.buf[:size],'sha256') 
        self.buf[size:size+16] = hm.digest()[:16]           # 把部分消息认证码赋值到密文之后
        self.buf[size+16:size+32]=iv                        # 消息认证码之后是nonce
        return self.buf[:size+32]                           # 返回待发送密文

    def decrypt_e2e(self,size):                             # 验证并解密，size是收到数据的长度
        if size <32: return None                            # 部分消息认证码+nonce=32
        msg = self.buf[:size-32]                            # 收到的加密消息
        hm = hmac.HMAC(self.e2e_key, msg,'sha256').digest()[:16]  # 计算hmac
        if hm != self.buf[size-32:size-16]:                 # 比对消息认证码
            return None        
        cipher = cryptolib.aes(self.e2e_key, 6, self.buf[size-16:size])  # 使用相同nonce定义解密对象
        cipher.decrypt(msg,msg)                             # 原地解密
        return msg                                          # 返回解密缓存
    
    def encrypt_send(self,msg):                             # 加密并发送消息
        data = self.encrypt_e2e(msg) 
        self.e.send(self.pmac,data,False) 
        
    def recv_decrypt(self):                                 # 接收并解密消息
        size = self.e.recvinto(self.buf_in) 
        return self.decrypt_e2e(size)
 
    def deinit(self):                                       # 反初始化
        self.e.active(False)
        self.sta.active(False)