import os, hashlib
from cryptolib import aes
MODE_CBC, MODE_CTR = 2, 6                     # 加密模式常量
msg = bytearray(b'这是一条待加密的消息')

# --------------------CBC模式加密和解密--------------------
def pad(msg:bytearray):                       # 原地填充函数
    x = 16-len(msg)%16
    msg.extend(chr(x)*x)
    return msg
def unpad(msg:bytearray):                     # 原地去除函数
    msg[-msg[-1]:]=b''
    return msg
key,iv = os.urandom(16),os.urandom(16)
aes(key,MODE_CBC,iv).encrypt(pad(msg),msg)    # 原地加密
aes(key,MODE_CBC,iv).decrypt(msg,msg)         # 原地解密
print(unpad(msg).decode())                    # 打印解密后信息

# --------------------CTR模式加密和解密--------------------
key = '12345678'                              # 用户设置的短密码
key_pad = hashlib.sha256(key).digest()[:16]   # 扩展密钥
aes(key_pad,MODE_CTR,iv).encrypt(msg,msg)     # 原地加密,iv使用
aes(key_pad,MODE_CTR,iv).decrypt(msg,msg)     # 原地解密
print(msg.decode())                           # 打印解密后信息
