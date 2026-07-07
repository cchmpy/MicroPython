from aiohttp import web
import ssl,socket,os
from binascii import b2a_base64
from zeroconf import ServiceInfo, Zeroconf
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec,rsa,padding 
from cryptography.hazmat.primitives.serialization import load_pem_private_key
class OTAServer:
    @staticmethod
    def ip():                                                    # 获取本机IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # 创建一个UDP socket
            s.connect(("114.114.114.114", 80))                   # 连到外部地址,或用8.8.8.8
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception: return None
    
    def __init__(self, firmware_file,cafile=None, keyfile=None):
        self._fw = firmware_file                                 # 固件文件路径
        self._ca = cafile                                        # 服务器证书文件
        self._key = keyfile                                      # 服务器私钥文件 
        # 读取固件文件 
        with open(self._fw, "rb") as f:                          # 读取固件
            self._bin = f.read()                                 # 变量bin保存文件内容
            self._bin_size = len(self._bin)                      # 固件文件大小(字节数) 
        # 定义固件请求的响应头
        self._headers={'Content-Type':'application/octet-stream',# 通用二进制流 
                       'Connection': 'close',
                       'Content-Disposition': 'attachment; filename="micropython.bin"', # 下载文件名
                       'Content-Length':str(self._bin_size)}     # 响应体长度（固件文件大小） 
        # 定义SSLContext对象、用私钥签名固件的哈希值
        self._ctx = None                                         # SSLContext对象
        self._sg = None                                          # 固件hash值的签名
        if self._key and self._ca:
            sha256_alg = hashes.SHA256()                         # 选用的hash算法
            digest = hashes.Hash(sha256_alg)                     # 哈希对象：计算固件哈希值
            digest.update(self._bin)
            h = digest.finalize()                                # 固件哈希值
            with open(self._key, 'rb') as f: 
                pkey = load_pem_private_key(f.read(), password=None)       # 载入私钥
            if isinstance(pkey, rsa.RSAPrivateKey):                        # 私钥使用了RSA算法
                self._sg = pkey.sign(h,padding.PSS(mgf=padding.MGF1(sha256_alg),
                                                   salt_length=padding.PSS.MAX_LENGTH),sha256_alg)                
            elif isinstance(pkey, ec.EllipticCurvePrivateKey):             # 私钥使用了ECDSA算法
                self._sg= pkey.sign(h,ec.ECDSA(sha256_alg))                # 用私钥签名
            if self._sg:
                sg = b2a_base64(self._sg,newline=False).decode()           # 签名→base64编码→str
                self._headers['Firmware-Signature']= sg                    # 自定义字段：签名数据
                self._ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)        # 定义SSLContext对象
                self._ctx.load_cert_chain(self._ca, self._key) 
            
    async def _ota(self,request):                                # '/ota'路径请求的处理协程
        return web.Response(headers=self._headers,body=self._bin)

    async def _index(self,request):                              # '/'主页请求的处理协程
        return web.Response(headers={'Content-Type': 'text/html; charset=utf-8',
                                     'Connection': 'close'},
                            body='<p>这是OTA固件更新网页<a href="/ota">[下载固件]</a></p>')
    
    def run(self,host='0.0.0.0',port=None,service_name='mpy-ota'):             # 运行服务器
        app = web.Application()
        app.add_routes([web.get('/ota', self._ota),web.get('/', self._index)]) # 路由分发
        ip = OTAServer.ip() 
        assert ip is not None 
        if port is None: port = 443 if self._ctx else 80
        proto = 'https' if self._ctx else 'http'
        if service_name:                                         # 启动域名服务(mDNS)
            service_info = ServiceInfo(
                f'_{proto}._tcp.local.',                         # 服务类型
                f'{service_name}._{proto}._tcp.local.',          # 设备名称
                addresses=[socket.inet_aton(ip)],                # 服务器IP
                port=port,                                       # 服务器端口
                server=f'{service_name}.local.')                 # 注册的本地域名
            zeroconf = Zeroconf()                                # 定义Zeroconf对象
            zeroconf.register_service(service_info)              # 注册服务
            print(f'OTA服务器 {proto}://{service_name}.local:{port} 已启动...')
        print(f'OTA服务器 {proto}://{ip}:{port} 已启动...') 
        try:                                                     # 启动服务器
            web.run_app(app, host=host, port=port, ssl_context=self._ctx) 
        finally:
            if service_name:
                zeroconf.unregister_service(service_info)
                zeroconf.close()
if __name__ == '__main__':
    ota = OTAServer(firmware_file='micropython.bin',
                        cafile='mpy-ota.local.pem', keyfile='mpy-ota.local-key.pem')
    ota.run()
