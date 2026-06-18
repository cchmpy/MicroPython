import hashlib
from cryptography import hashes,x509,serialization,ec
with open('mpy.bin','rb') as f:                                          # 计算固件文件的哈希值
    sha256 = hashlib.sha256()
    buf_size = 4096
    buf = memoryview(bytearray(buf_size))                                # 读取文件缓冲
    while (size := f.readinto(buf)):
        if size==buf_size: sha256.update(buf)
        else: sha256.update(buf[:size])
    digest = sha256.digest()    
with open('esp32-ec-key.der', 'rb') as f: 
    private_key = serialization.load_der_private_key(f.read(),None)      # 读取私钥
    signature = private_key.sign(digest, ec.ECDSA(hashes.SHA256()))      # 用私钥签名
with open('esp32-ec.der', 'rb') as f:  
    _ca = x509.load_der_x509_certificate(f.read())                       # 读取证书
    public_key = _ca.public_key()                                        # 提取公钥
    try:
        public_key.verify(signature, digest, ec.ECDSA(hashes.SHA256()))  # 用公钥验签
        print('签名验证成功(EC)!')
    except:
        print('签名验证失败(EC)!')  
