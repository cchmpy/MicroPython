from esp32 import Partition
from machine import reset
from sys import exit
import hashlib, asyncio, ssl
from otaclient import OTAClient  # 导入程序11-18.py（otaclient.py）
import time
try:
    from cryptography import hashes, rsa, ec, padding, x509          # 载入第三方加密算法库
    VERIFY_SIG = True                                                # 验证签名
except ImportError:
    VERIFY_SIG = False                                               # 不验证签名 

class OTA:
    @staticmethod
    def mark_cancel_rollback():                                      # 新建或更新main.py，禁止回滚
        def _write(f):                                               # 嵌套函数，写入main.py
            f.seek(0)                                                # 定位到文件开头
            f.write('from esp32 import Partition\n')
            f.write('Partition.mark_app_valid_cancel_rollback()\n')
        try:
            with open('/main.py','r+') as f:                         # 文件存在
                data = f.read()
                if 'Partition.mark_app_valid_cancel_rollback()' not in data:
                    _write(f)                                        # 写入禁止回滚函数
                    f.write(data)                                    # 写入main.py的原内容
        except OSError:                                              # main.py不存在,抛出异常
            with open('/main.py','w') as f:  _write(f)               # 新建并写入
    
    def __init__(self):
        try:
            self._ota=Partition(Partition.RUNNING).get_next_update() # 获取更新分区，非OTA分区抛出OSError            
            bs = self._ota.ioctl(5,0)                                # 获取块大小:4096字节
            self._block_size = bs if bs else 512                     # 若iotcl()返回None，则使用默认值512
            self._blocks = self._ota.ioctl(4,0)                      # 分区总块数
            self._psize  = self._block_size * self._blocks           # 分区大小
            self._buf = memoryview(bytearray(self._block_size))      # 读写缓冲（大小与分区块相同）            
        except OSError: 
            print('× 设备使用了非OTA固件，无法更新')
            exit(0)                                                  # 退出并软重置系统
    
    def _erase(self):                                                # 擦除OTA更新分区
        b = self._blocks
        ota = self._ota
        print('  现在擦除OTA更新分区，已完成：')        
        for i in range(b):
            ota.ioctl(6,i)                                           # 擦除第i块
            print(f'  {(i+1)*100//b}%\r',end='')                     # 打印擦除进度
        print('\n√ 完成擦除')
    
    def _reset(self):                                                # 设置启动分区、禁止回滚、硬重置        
        print('√ 固件更新成功')
        print(f'  当前运行分区：{Partition(Partition.RUNNING).info()[4]}')
        print(f'  下次启动分区：{self._ota.info()[4]}')
        self._ota.set_boot()                                         # 设置启动分区
        OTA.mark_cancel_rollback()                                   # 重启成功后，禁止回滚
        print('  现在硬重置...')
        reset()
    
    def _partition_digest(self,size):                                # 获取已写入更新分区数据的摘要
        # 参数size：写入分区的总字节数
        buf = self._buf
        blocks,left = divmod(size,self._block_size)                  # 写入的整数块数、剩余字节数
        sha256 = hashlib.sha256()                                    # 定义hash对象
        for i in range(blocks): 
            self._ota.readblocks(i,buf,0)                            # 整块读取
            sha256.update(buf)
        b = buf[:left]
        self._ota.readblocks(blocks,b,0)                             # 读取剩余
        sha256.update(b) 
        return sha256.digest()                                       # 返回摘要
    
    def update_from_file(self, bin_file):                            # 从文件更新
        bs = self._block_size                                        # 分区块大小（局部变量缓存实例变量）
        buf = self._buf                                              # 缓存
        
        # 1、打开文件、检查文件和分区大小、擦除分区
        try: f = open(bin_file,'rb')
        except OSError:
            print(f'× 无法打开固件文件,它可能不存在')
            return None
        fsize = f.seek(0,2)                                          # 固件文件总大小
        f.seek(0)                                                    # 定位到文件开头
        if fsize+bs > self._psize:                            # 检查分区大小是否满足固件要求(冗余一个扇区)
            print(f'× 固件文件大小[{fsize}]接近或超过分区容量[{self._psize}]，无法更新')
            return None
        self._erase()                                                # 擦除分区
    
        # 2、将固件写入ota分区
        print('  写入固件文件...')
        file_digest = hashlib.sha256()                               # 用于计算固件文件的sha256摘要
        block_id = 0                                                 # 待写入分区块编号
        t = 0                                                        # 写入分区总字节书
        while size := f.readinto(buf):                               # 读取固件
            if size != bs: buf = buf[:size]                          # 读取到文件末尾
            self._ota.writeblocks(block_id,buf,0)                    # 写入块
            file_digest.update(buf) 
            block_id += 1                                            # 下一个块
            t += size                                                # 更新写入总字节数
        print('√ 完成写入')
        f.close()                                                    # 关闭文件
        
        # 3、哈希值校验
        if file_digest.digest() != self._partition_digest(t):        # 对比文件和写入ota固件的哈希值
            print('× 哈希值(SHA256)校验错误，更新失败')
            return None
        else: print('√ 哈希值(SHA256)校验正确')
        
        # 4、设置启动分区、禁止回归、硬重置
        self._reset()
        
    async def _update(self, host, path, port, server_cert, firmware_sig_cert):
        global VERIFY_SIG
        # 1、定义ctx对象，用于ssl验证服务器身份
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)                # 创建客户端模式的SSLContext
        if server_cert:                                              # 提供验证服务器身份的证书文件
            ctx.load_verify_locations(cafile=server_cert)            # 载入证书链数据
            ctx.verify_mode = ssl.CERT_REQUIRED                      # 验证服务器身份
        else: ctx.verify_mode = ssl.CERT_NONE                        # 不验证服务器身份
        
        # 2、连接服务器、请求固件文件、验证固件文件与分区大小关系、擦除分区
        s = OTAClient(timeout=10)
        r = await s.get(host=host, path=path, port=port, ssl=ctx)    # GET请求固件
        if r is None:
            return None        
        fsize = r.headers['content-length']                          # 固件文件大小
        bs = self._block_size                                        # 闪存分区的块大小
        if (fsize+bs) > self._psize:                                 # 分区内预留一个块的冗余量
            print(f'× 固件文件大小[{fsize}]接近或超过分区容量[{self._psize}]，无法更新')
            return None 
        self._erase()                                                # 擦除分区
        
        # 3、分块读取并写入ota分区
        print('  分块读取固件并写入OTA分区...')
        file_digest = hashlib.sha256()                               # 下载固件文件的sha256对象
        block_id = 0                                                 # 待写入分区块编号
        t = 0                                                        # 写入分区总字节书
        reader = r.reader       
        while True:
            remain = fsize - t                                       # 固件的剩余未读取字节数
            if remain>=bs: data = await reader.readexactly(bs)                
            elif remain>0: data = await reader.readexactly(remain)                
            else:  break
            self._ota.writeblocks(block_id,data,0)                   # 写入块
            file_digest.update(data)
            block_id += 1
            t += len(data)
            print(f'  {t*100//fsize}%\r',end='')                     # 打印读取和写入进度
        await r.close()                                              # 异步关闭客户端连接
        print('\n√ 完成写入')
        
        # 4、哈希值校验或使用公钥验证签名
        sg = r.headers.get('firmware-signature',None)                # 服务器端的固件签名，可能没有
        VERIFY_SIG = VERIFY_SIG and bool(sg) and bool(firmware_sig_cert) # 是否需要验签
        if VERIFY_SIG == False:                                      # 不使用公钥验签
            if file_digest.digest() != self._partition_digest(t):    # 对比文件和写入ota固件的哈希值
                print('× 哈希值(SHA256)校验错误，更新失败')
                return None
            print('√ 哈希值(SHA256)校验正确') 
        else:                                                        # 使用公钥验签
            with open(firmware_sig_cert, 'rb') as f:                 # 读取用于验证签名的服务器证书
                ca = x509.load_der_x509_certificate(f.read())        # 载入公钥证书
                pkey = ca.public_key()                               # 提取公钥 
            sha256_alg = hashes.SHA256()                             # 选用的哈希算法
            if isinstance(pkey, rsa.RSAPublicKey):                   # 公钥算法:RSA 
                try:
                    pkey.verify(sg, self._partition_digest(t),       # 用公钥验签
                                padding.PSS(mgf=padding.MGF1(sha256_alg),
                                            salt_length=sha256_alg.digest_size),
                                sha256_alg)
                except:
                    print('× 签名验证失败!(RSA)')
                    return None
            elif isinstance(pkey, ec.EllipticCurvePublicKey):        # 公钥算法:ECDSA 
                try:
                    pkey.verify(sg, self._partition_digest(t), ec.ECDSA(sha256_alg))  # 用公钥验签
                except:
                    print('× 签名验证失败!(ECDSA)')
                    return None
            print('√ 签名验证成功')
           
        # 5、设置启动分区、禁止回滚、硬重置
        self._reset()
    
    def update_from_http(self, host, path, port=None, server_cert=None, firmware_sig_cert=None):
        asyncio.run(self._update(host=host, path=path, port=port,
                                 server_cert=server_cert, firmware_sig_cert=firmware_sig_cert))

if __name__=='__main__':
    import myutils
    myutils.connect_wifi()
    myutils.sync_ntp()
    ota = OTA()
    ota.update_from_http(host='mpy-ota.local', path='/ota', 
                         server_cert='rootCA.der', firmware_sig_cert='mpy-ota.local.der')

