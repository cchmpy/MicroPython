import os
from cryptography import rsa, padding, hashes
key = os.urandom(16)                                    # 待交换的密钥
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048) # 生成私钥
public_key  = private_key.public_key()                                       # 获取公钥
oaep = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),  # RSA加密中的OAEP填充方案
                    algorithm=hashes.SHA256(),
                    label=None)    

encrypted = public_key.encrypt(key,oaep)                # 使用公钥加密
decrypted = private_key.decrypt(encrypted,oaep)         # 使用私钥解密
print(key == decrypted)                                 # 判断解密后的数据与原始数据是否相同 
