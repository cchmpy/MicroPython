import hashlib, os
from esp32 import NVS
from micropython import const
# 定义常量：用户存在、用户不存在、用户名太长
_USER_EXISTS=const(1); _ERR_NOT_EXISTS=const(2); _ERR_TOO_LONG=const(3)
class UserReg:
    @staticmethod                              # 简化版pbkdf2算法
    def _pbkdf2_sha256(psw, salt=None, iterations=1000): 
        if salt is None: salt = os.urandom(16) # 自动加盐：16字节真随机数
        digest = psw.encode()                  # str->bytes
        for _ in range(iterations):            # 多次哈希迭代
            digest=hashlib.sha256(digest+salt).digest()   # 盐值+密码->SHA256
        return salt,digest                     # 返回盐值和加密哈希值
    
    def __init__(self,nvs_namespace='users'): 
        self._nvs = NVS('users')               # 创建命名空间为users的NVS对象
        self._buf = bytearray(64)              # 读取NVS内信息时的缓存
        
    def _user_exists(self,name):               # 判断用户是否存在
        if len(name.encode())>15:  return _ERR_TOO_LONG   # nvs的key最多15个字节
        try:        
            self._nvs.get_blob(name, self._buf)# 若用户名存在，读取哈希密码
            return _USER_EXISTS
        except OSError as err:                 # 若name不存在,get_blob()抛出OSError
            return _ERR_NOT_EXISTS
 
    def register(self,name,psw):               # 用户注册并保存密码哈希值
        e = self._user_exists(name)
        if e==_ERR_TOO_LONG:  return f'用户名"{name}"太长' 
        elif e==_USER_EXISTS: return '用户名已经存在'
        elif e==_ERR_NOT_EXISTS:
            salt,digest = self._pbkdf2_sha256(psw)
            # 保存值: salt长度+salt+digest
            self._nvs.set_blob(name,len(salt).to_bytes(1) +salt+digest)  
            self._nvs.commit(); return '注册成功' # 将set操作提交闪存
        else: return '其它错误'
    
    def verify(self, name, psw):                # 验证用户名和密码
        e = self._user_exists(name)             # 读入加密哈希到_buf
        if e==_USER_EXISTS:
            i = self._buf[0]                    # 盐值长度  
            _,new_digest = self._pbkdf2_sha256(psw,self._buf[1:i+1]) 
            return new_digest == self._buf[i+1:i+33]    
        return False
if __name__ == '__main__':
    ur = UserReg()    
    print(ur.register('user1','12345678'))
    print(ur.verify('user1','12345678')) 
    print(ur.verify('user1','1sxf1255')) 
