from machine import Pin
from micropython import const
import time
_WRITE_ENABLE     = const(0x06)    # 写使能指令
_READ_STATUS_REG1 = const(0x05)    # 读取状态寄存器-1指令
_PAGE_PROGRAM     = const(0x02)    # 页面编程指令
_READ_DATA        = const(0x03)    # 普通读取指令
_FAST_READ        = const(0x0B)    # 快速读取指令
_POWER_DOWN       = const(0xB9)    # 关机指令
_RELEASE_POWER_DOWN=const(0xAB)    # 释放关机指令（唤醒）
_READ_JEDEC_ID    = const(0x9F)    # 读取JEDEC ID
_READ_UNIQUE_ID   = const(0x4B)    # 读取64位唯一序列号(并非所有设备都支持该指令)
_PAGE_SIZE        = const(0x100)   # 页面大小：256字节

class NORFlash25: 
    SECTOR_ERASE    = 0x20         # 扇区(4KiB)擦除指令
    BLOCK_32K_ERASE = 0x52         # 32KiB块擦除指令
    BLOCK_64K_ERASE = 0xD8         # 64KiB块擦除指令
    CHIP_ERASE      = 0xC7         # 芯片整体擦除指令
    
    def __init__(self, spi, cs):
        self._spi = spi
        self._cs = Pin(cs,mode=Pin.OUT, value=1)                # 片选，初始化为高电平(禁用)
        self._mid, self._mtype, self._flash_size = self.read_JEDEC_id()     # 读取JEDEC ID 
        self._addr_len=4 if self._flash_size>0x100_0000 else 3  # 指令地址的长度(16MiB以上为4)
        
        self._cmd_buf = bytearray(self._addr_len+1)             # 指令的缓存（指令+地址)
        self._fread_buf = bytearray(self._addr_len+2)           # 快速读取指令的缓存
        self._status_buf = bytearray(1)                         # 状态寄存器-1读取缓冲区
    
    def __len__(self):                                          # 实现len(NORFlash25)接口
        return self._flash_size
    
    def __str__(self):
        return f'制造商ID: 0x{self._mid:02X},存储类型: 0x{self._mtype:02X},容量: {self._flash_size>>10}KiB'
                
    def read_JEDEC_id(self):                                    # 读取制造商ID、存储类型、字节容量
        self._cs(0)
        self._spi.write((_READ_JEDEC_ID).to_bytes(1))           # 发送指令
        id_data = self._spi.read(3)                             # 读取：制造商ID(1)+存储类型(1)+容量(1)
        self._cs(1)
        return id_data[0],id_data[1], 2**(id_data[2])           # 返回读取结果

    def read_unique_id(self):                                   # 读取64位唯一序列号 
        self._cs(0)
        self._spi.write(bytes((_READ_UNIQUE_ID, 0x00, 0x00, 0x00, 0x00)))  # 发送指令+4字节空闲信号
        uid = self._spi.read(8)                                 # 读取8字节序列号
        self._cs(1)
        return uid
      
    def _check_addr(self, addr):                                # 检查参数addr是否处于正常范围
        if addr < 0 or addr >= self._flash_size:
            raise ValueError(f'地址超出范围：0x{addr:X} (最大0x{self._flash_size:X})')
        
    def _write_cmd(self, cmd, addr):                            # 发送指令+地址
        self._cmd_buf[0] = cmd                                  # 指令码
        a = self._addr_len                                      # 地址的字节长度（3或4）
        for i in range(a-1, -1, -1): 
            self._cmd_buf[a-i] = (addr >> i*8) & 0xFF           # 将地址赋值到缓冲self._cmd_buf 
        self._spi.write(self._cmd_buf)                                     
    
    def _write_read_cmd(self,addr, fast_read):                  # 发送读取/快速读取指令
        if fast_read:
            self._fread_buf[0] = _FAST_READ                     # 快速读取指令码
            a = self._addr_len
            for i in range(a-1, -1, -1): 
                self._fread_buf[a-i] = (addr >> i*8) & 0xFF     # 地址码（3字节或4字节）
            self._spi.write(self._fread_buf)                    # _fread_buf最后的字节是空闲信号(任意值)
        else:
            self._write_cmd(_READ_DATA, addr)                   # 发送普通读取指令
        
    def readinto(self, addr, buf, fast_read=False):             # 从地址addr读取数据到buf
        if len(buf)<1: return
        self._check_addr(addr+len(buf)-1)                       # 检查地址
        self._cs.value(0)
        self._write_read_cmd(addr, fast_read)
        self._spi.readinto(buf)                                 # 读取数据到缓冲区
        self._cs(1)
    
    def read(self, addr, nbytes, fast_read=False):              # 从地址addr读取nbytes字节的数据
        if nbytes<1: return b''
        self._check_addr(addr+nbytes-1) 
        self._cs.value(0)
        self._write_read_cmd(addr, fast_read)
        data = self._spi.read(nbytes)
        self._cs(1)
        return data     
    
    def _wait_busy(self):                                       # 等待状态寄存器-1的BUSY位由1并为0
        self._cs(0) 
        self._spi.write(_READ_STATUS_REG1.to_bytes(1))          # 发送“读取状态寄存器-1”指令
        while True:                                             # 轮询BUSY位（状态寄存器第0位）
            self._spi.readinto(self._status_buf)
            if (self._status_buf[0] & 0x01) == 0:               # 检查BUSY位（比特0位）
                break
            time.sleep_us(10)                                   # 短暂等待
        self._cs(1) 

    def _write_enable(self):                                    # 发送写使能指令，解锁写入/擦除权限 
        self._cs(0)
        self._spi.write(_WRITE_ENABLE.to_bytes(1))
        self._cs(1)
        time.sleep_us(10)                                       # 延时等待指令生效
        
    def erase(self, erase_type, addr=None):                     # 擦除
        if erase_type != NORFlash25.CHIP_ERASE:                 # 非芯片整体擦除时检查地址
            self._check_addr(addr)
        self._write_enable()                                   # 获取写权限
        self._cs(0)
        if erase_type != NORFlash25.CHIP_ERASE:
            self._write_cmd(erase_type, addr)                  # 发送擦除指令+地址
        else:
            self._spi.write(erase_type.to_bytes(1))            # 芯片擦除指令
        self._cs(1)
        self._wait_busy()

    def _page_program(self, addr, data):                       # 底层页编程:单次写入≤256字节，不跨页
        if len(data) == 0 or len(data) > _PAGE_SIZE:
            raise ValueError(f'页写入长度必须1-{_PAGE_SIZE}字节')
        self._write_enable()
        self._cs.value(0)
        self._write_cmd(_PAGE_PROGRAM, addr)                   # 发送指令码
        self._spi.write(data)                                  # 发送数据
        self._cs(1)
        self._wait_busy()                                      # 等待完成编程

    def write(self, addr, data):                               # 批量写入数据，自动处理跨页
        # 参数addr: 起始写入地址； 参数data: bytes/bytearray/memoryview 数据（任意长度）
        data_idx = 0                                           # data对象的索引，将从该索引开始写入
        remaining = len(data)                                  # 剩余数据（待写入）的字节长度
        current_addr = addr                                    # 从当前地址开始写入
        while remaining > 0:
            self._check_addr(current_addr)
            page_offset = current_addr % _PAGE_SIZE                               # 当前页的写入起始地址
            write_len = min(remaining, _PAGE_SIZE - page_offset)                  # 当前页可写入字节数
            self._page_program(current_addr, data[data_idx:data_idx+write_len])   # 写入当前页 
            # 更新状态
            data_idx += write_len
            remaining -= write_len
            current_addr += write_len

    def power_down(self,mode=True):                            # 进入(True)或退出(False)掉电模式
        cmd = _POWER_DOWN if mode else _RELEASE_POWER_DOWN 
        self._cs(0)
        self._spi.write(cmd.to_bytes(1))
        self._cs(1)
        time.sleep_us(10)
if __name__ == "__main__":
    from machine import SPI     
    spi = SPI(2, 10_000_000, sck=16, mosi=17, miso=5) 
    flash = NORFlash25(spi, 22)
    print(flash)
    size, addr = 16, 0x1000                                    # 要读取数据的字节数, 地址
    buf = bytearray(size)
    for i in range(2):                                         # 普通读取和快速读取
        print(flash.read(addr,size))
        flash.readinto(addr,buf)
        print(buf)
