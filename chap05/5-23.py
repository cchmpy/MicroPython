from cryptography import hashes, ec, rsa, padding
_hash = hashes.SHA256()                                  # 选用的哈希算法
msg = b'用于签名的消息'
sha256 = hashes.Hash(_hash)
sha256.update(msg)
digest = sha256.finalize()                               # 用于签名的哈希值

#-------------------------RSA算法签名与验签-------------------------
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)   # 生成私钥
public_key = private_key.public_key()                                          # 生成公钥
_pad = padding.PSS(mgf=padding.MGF1(_hash), salt_length=_hash.digest_size)     # 填充算法
signature = private_key.sign(digest,_pad,_hash)           # 用私钥签名
try:
    public_key.verify(signature, digest,_pad, _hash)      # 用公钥验签
    print('签名验证成功(RSA)!')
except:
    print('签名验证失败(RSA)!')
#-------------------------ECDSA算法签名与验签-------------------------
private_key = ec.generate_private_key(ec.SECP256R1())     # 生成私钥
public_key = private_key.public_key()                     # 生成公钥
signature = private_key.sign(digest, ec.ECDSA(_hash))     # 用私钥签名
try:
    public_key.verify(signature, digest+b'a', ec.ECDSA(_hash))    # 用公钥验签，修改digest导致验签失败
    print('签名验证成功(EC)!')
except:
    print('签名验证失败(EC)!')
