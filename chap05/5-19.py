import hashlib, os
from esp32 import NVS
from micropython import const
# 定义常量
_USER_EXISTS     = const(1)                                  # 用户存在
_ERR_NOT_EXISTS  = const(0)                                  # 用户不存在
_ERR_OTHER       = const(2)                                  # 其它错误
_ERR_TOO_LONG    = const(3)                                  # 用户名太长

# 定义全局变量  
_nvs = NVS('users')                                          # 创建命名空间为users的NVS对象
_buf = bytearray(64)                                         # 读取NVS内信息时的缓存

# 简化版pbkdf2算法
def pbkdf2_sha256(psw:str, salt=None, iterations=1000):
    if salt is None: salt = os.urandom(16)                   # 自动加盐，生成16字节真随机数作为盐值
    digest = psw.encode()
    for _ in range(iterations):                              # 多次哈希迭代,NIST建议>=10万次
        digest = hashlib.sha256(digest + salt).digest()      # 盐值+密码->SHA256
    return salt,digest                                       # 返回盐值和加密哈希值

# 判断用户是否存在
def _user_exists(name):
    if len(name.encode())>15: return _ERR_TOO_LONG           # 用户名太长,nvs的key最多15个字节
    try:        
        _nvs.get_blob(name, _buf)                            # 若用户名存在，读取哈希密码读到缓存
        return _USER_EXISTS
    except OSError as err:                                   # 若name不存在,get_blob()抛出OSError
        if err.errno == -4354:                               # 用户名不存在，错误码可以通过打印err获取
            return _ERR_NOT_EXISTS
        else:                                                # 其它错误
            print(err)
            return _ERR_OTHER

# 用户注册并保存密码哈希值
def register_user(name,psw): 
    e = _user_exists(name)
    if e==_ERR_TOO_LONG:  info=f'用户名"{name}"太长,最多15个英文字符或5个汉字!' 
    elif e==_USER_EXISTS: info='用户名已经存在'
    elif e==_ERR_NOT_EXISTS:
        salt,digest = pbkdf2_sha256(psw)
        _nvs.set_blob(name,len(salt).to_bytes(1)+salt+digest) # 保存值: salt长度+salt+digest
        _nvs.commit()                                         # 将set操作提交闪存
        info = '注册成功'
    else: info = '其它错误'
    return info

# 验证用户名和密码
def verify_pbkdf2(name, psw):
    e = _user_exists(name)                                   # 读入加密哈希到_buf
    if e==_USER_EXISTS:
        i = _buf[0]                                          # 盐值长度  
        _,new_digest = pbkdf2_sha256(psw,_buf[1:i+1]) 
        return new_digest == _buf[i+1:i+33]    
    return False

if __name__ == '__main__':   
    print(register_user('cch','12345678'))
    print(verify_pbkdf2('cch','12345678')) 
    print(verify_pbkdf2('cch','1sxf1255')) 
