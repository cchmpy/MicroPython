# 用于读取gb16x16.bin文件或烧录到Flash的数据
from micropython import const
import esp
_STEP  = const(3)                              # 索引头的每个码位存储3个字节的点阵数据的地址
_BASE1 = const(0)                              # 0x0000-0x0451区间的unicode编码对应的起始地址
_BASE2 = const(_BASE1+0x0452*_STEP)            # 0x2015-0x2642
_BASE3 = const(_BASE2+(0x2642-0x2015+1)*_STEP) # 0x3000-0x3229
_BASE4 = const(_BASE3+(0x3229-0x3000+1)*_STEP) # 0x4E00-0x9FA0
_BASE5 = const(_BASE4+(0x9FA0-0x4E00+1)*_STEP) # 0xFF01-0xFFE5

class Font:
    BUF = memoryview(bytearray(35)) # 类属性,缓存读取数据,前3个保存地址数据,它被所有派生类实例对象共用
    def read(self,s,offset):        # offset是含索引头的点阵数据在flash中的起始地址,若从文件读取则为0
        uni = ord(s[0])                     # Unicode编码
        size = (16 if uni<=0x7f else 32)    # ASCII字符点阵数据为16字节
        if uni<=0x0451: addr = _BASE1+uni*_STEP
        elif 0x2015<=uni<=0x2642: addr = _BASE2+(uni-0x2015)*_STEP
        elif 0x3000<=uni<=0x3229: addr = _BASE3+(uni-0x3000)*_STEP
        elif 0x4E00<=uni<=0x9FA0: addr = _BASE4+(uni-0x4E00)*_STEP
        elif 0xFF01<=uni<=0xFFE5: addr = _BASE5+(uni-0xFF01)*_STEP
        else: addr=0  
        if addr:
            addr += offset                  # 加上偏移地址 
            self._read(addr,self.BUF[:3])   # 使用派生类的成员函数_read()读取3个字节点阵数据的地址
            if b'\x00\x00\x00'<self.BUF[:3]<=b'\x04\xC6\x20': # 判断地址有效性,字库文件大小是0x04c620
                addr_bm = (self.BUF[0]<<16)+(self.BUF[1]<<8)+self.BUF[2]+offset # 计算地址 
                self._read(addr_bm,self.BUF[3:size+3])                          # 读取点阵数据 
                return size>>1,16,self.BUF[3:size+3]                            # 返回w,h,memoryview对象
        self.BUF[3:35]=bytes(32)            # 不能识别的字符,点阵数据用0填充 
        return 16,16,self.BUF[3:35]         # 返回一个空的占位符
        
class Flash(Font): 
    def _read(self,addr,buf):
        esp.flash_read(addr,buf)
        
class File(Font):
    def __init__(self,font_file='gb16x16.bin'):
        try: self._f = open(font_file,'rb') 
        except OSError: self._f = None 
    def deinit(self):
        if self._f: self._f.close() 
    def _read(self,addr,buf):
        self._f.seek(addr)
        self._f.readinto(buf)
           
if __name__=='__main__':
    bm = Flash().read('啊',0x380000)          # 使用方式4读取数
    if bm: print(bm[0],bm[1],bytes(bm[2]))    
    
    fon = File()
    bm = fon.read('啊',0)                     # 使用方式3读取数
    if bm: print(bm[0],bm[1],bytes(bm[2])) 
    fon.deinit() 
