from esp32 import Partition
from machine import reset
from sys import exit
import hashlib

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
        print('\n√ 完成写入')
        f.close()                                                    # 关闭文件
        
        # 3、哈希值校验
        if file_digest.digest() != self._partition_digest(t):        # 对比文件和写入ota固件的哈希值
            print('× 哈希值(SHA256)校验错误，更新失败')
            return None
        else: print('√ 哈希值(SHA256)校验正确')
        
        # 4、设置启动分区、禁止回归、硬重置
        self._reset()
        
if __name__=='__main__':
    ota = OTA()
    ota.update_from_file('/sd/micropython.bin')