import struct
from gc import collect
from notflash25 import NORFlash25
from micropython import const
_PAGE_SIZE = const(256)                                     # 页面大小

class BurnFlash:
    def __init__(self, spi, cs):
        self.flash = NORFlash25(spi, cs)                    # flash是NORFlash25对象            
        self._size = len(self.flash)                             # 获取闪存大小       
        
    def write(self, font_file, erase=True):                 # 写入二进制字模文件               
        # 1、打开文件、检查文件和分区大小
        try: f = open(font_file,'rb')
        except OSError:
            print(f'× 无法打开字模文件,它可能不存在')
            return None
        fsize = f.seek(0,2)                                 # 字库文件总大小
        f.seek(0)                                           # 定位到文件开头
        if fsize > self._size:                              # 检查闪存大小是否满足要求
            print(f'× 字模文件大小[{fsize}]超过闪存容量[{self._size}]，无法写入')
            return None        
        # 2、擦除整个闪存
        if erase:
            print('  擦除目标闪存...')
            self.flash.erase(erase_type=self.flash.CHIP_ERASE)
            print('  √ 完成擦除')        
        # 3、将文件写入闪存、校验数据
        buf1 = bytearray(_PAGE_SIZE)                        # 读取文件缓存
        buf2 = bytearray(_PAGE_SIZE)                        # 读取闪存缓存，用于验证 
        print('  写入字模文件...')
        addr = 0                                            # 待写入地址（也是写入闪存总字节数）        
        while size := f.readinto(buf1):                     # 读取文件          
            if size != _PAGE_SIZE:                          # 读取到文件末尾
                buf1 = buf1[:size]                          
            self.flash.write(addr,buf1)                     # 写入闪存            
            self.flash.readinto(addr,buf2)                  # 读取已写入闪存的数据
            verify_err = (buf1!=buf2[:size]) if size!=_PAGE_SIZE else (buf1!=buf2) # 简单校验
            if verify_err:                                  # 校验出现错误
                f.close()
                raise ValueError(f'地址0x{hex(addr)}处的数据校验错误')            
            addr += size                                    # 更新闪存写入地址            
            print(f'  {addr*100//fsize}%\r',end='')         # 打印写入进度
        print('\n  √ 完成写入,已通过数据验证')
        f.close()                                           # 关闭文件

class Font:                                                 # 二进制字库文件解析驱动类 
    _instance = None
    LF_WIDTH    = const(-1)                                 # 特殊标记：换行符Line Feed的宽度
    CR_WIDTH    = const(-2)                                 # 特殊标记：回车符Carriage Return的宽度
    
    def __new__(cls, *args, **kwargs):                      # 限制该类只能创建单例对象
        if cls._instance is None: cls._instance = super().__new__(cls) 
        return cls._instance   

    def __init__(self, spi, cs):        
        self._gb_buf = bytearray(2)                         # 保存GB2312编码的缓冲
        self.flash = NORFlash25(spi, cs)                    # flash是NORFlash25对象        
        self._desc = {}                                     # 描述所有字模集信息的字典
        
        header = self.flash.read(0,16)                      # 读取文件基础头(16字节) 
        d = struct.unpack('>4sHIHI', header)                # 解包文件头        
        # 解包结果：魔数、字模描述项数量、字模描述表地址、是否分段索引GB2312编码、GB2312编码地址
        magic, desc_count, desc_addr, self._seg_idx, self._BASE1 = d 
        if magic != b'FONT': raise ValueError("闪存内不是有效字库数据（魔数不匹配）") 
        if self._seg_idx:                                   # 初始化分段索引GB2312编码的各段地址
            self._BASE2 = self._BASE1+(0x0451-0x0000+1)*2
            self._BASE3 = self._BASE2+(0x2642-0x2015+1)*2
            self._BASE4 = self._BASE3+(0x3229-0x3000+1)*2
            self._BASE5 = self._BASE4+(0x9FA0-0x4E00+1)*2
                     
        for i in range(desc_count):                         # 遍历所有描述表            
            desc_data = self.flash.read(desc_addr,12)       # 读取一种字模集的描述项（12字节）
            # 字模集信息：字符集(1是ASCII,2是GB2312)、像素宽、像素高、单字模字节长度、字模偏移地址
            charset, w, h, size, addr = struct.unpack('>4HI', desc_data)            
            v = self._desc.get(h,None)                      # 以h为键，查询值
            if v is None: v = self._desc[h] = {}            # 添加键值对（值也是字典对象）
            if charset==1: v['asc_w']=w; v['asc_size']=size; v['asc_addr']=addr
            else:          v['gb_w']=w;  v['gb_size']=size;  v['gb_addr']=addr
            desc_addr += 12        
        collect()                                           # 手动执行垃圾收集
       
    def __str__(self):                                      # 返回字模信息字符串（如asc6x12/gb12x12)
        sorted_items = sorted(self._desc.items())           # 取得按键排序的元组
        buf = bytearray() 
        for h, d in sorted_items:                           # 遍历元组所有数据项
            buf.extend(f'asc{d["asc_w"]}x{h}\ngb{d["gb_w"]}x{h}\n') # 添加字模集信息，如asc6x12、gb12x12
        return buf.decode()
        
    def gb2312(self, uni):                                  # 返回Unicode码位uni的gb2312编码
        if self._seg_idx:                                   # 用Unicode码位分段索引
            if uni<=0x0451:           addr = self._BASE1+uni*2
            elif 0x2015<=uni<=0x2642: addr = self._BASE2+(uni-0x2015)*2
            elif 0x3000<=uni<=0x3229: addr = self._BASE3+(uni-0x3000)*2
            elif 0x4E00<=uni<=0x9FA0: addr = self._BASE4+(uni-0x4E00)*2
            elif 0xFF01<=uni<=0xFFE5: addr = self._BASE5+(uni-0xFF01)*2
            else: addr=self._BASE1                          # uni是空码位或超越索引范围，地址设为空码位
        else:                                               # 用Unicode码位直接索引
            if uni>0xFFE5: addr=self._BASE1                 # uni超出索引, 地址设为GB2312的空码位
            else:          addr=self._BASE1+uni*2           # _BASE1是GB2312编码的起始地址         
        buf = self._gb_buf
        self.flash.readinto(addr, buf)                         # 读取GB2312编码到缓冲区（2字节）
        if buf[0]>0xFE or buf[0]==0:                        # 无法识别字符返回的GB2312编码是0xFFFF或0x0
            buf[0]=buf[1]=0xA1                              # 用全角空格代替无法识别字符
        return buf 
     
    def pixel_h(self):                                       # 返回文件中所有字模集的像素高度（元组）
        return (self._desc.keys())
        
    def size(self, h, asc = True):                           # 返回像素高度为h单个字模的字节长度
        v = self._desc.get(h,None)
        if v: return v.get('asc_size',0) if asc else v.get('gb_size',0)
        else: return 0
   
    def read(self, s, h):
        v = self._desc.get(h,None)
        if v is None: raise ValueError(f'字库不包含像素高度为{h}的字模')
        asc_w=v['asc_w']; asc_size=v['asc_size']; asc_addr=v['asc_addr']
        gb_w=v['gb_w'];   gb_size=v['gb_size'];   gb_addr=v['gb_addr']        
        for c in s:                                          # 遍历字符串s            
            uni = ord(c)
            if uni < 127:                                    # ASCII
                if uni>31:                                   # 可显示字符 
                    addr = asc_addr + uni*asc_size
                    yield asc_w,h, self.flash.read(addr, asc_size)
                elif uni==10: yield LF_WIDTH, h, b''         # 换行符
                elif uni==13: yield CR_WIDTH, h, b''         # 回车符
            else:                                            # GB2312
                gb_code = self.gb2312(uni)
                addr = gb_addr + ((gb_code[0]-0xA1)*94+gb_code[1]-0xA1)*gb_size                
                yield gb_w,h, self.flash.read(addr,gb_size)     # 返回字符对应的像素宽度、高度、字模
            
    def readinto(self, s, h, *, asc_buf=None, gb_buf=None):
        v = self._desc.get(h,None)
        if v is None: raise ValueError(f'字库不包含像素高度为{h}的字模')
        if asc_buf: asc_w=v['asc_w']; asc_size=v['asc_size']; asc_addr=v['asc_addr']
        if gb_buf:  gb_w=v['gb_w'];   gb_size=v['gb_size'];   gb_addr=v['gb_addr']
        for c in s:                                          # 遍历字符串            
            uni = ord(c)
            if uni < 127:                                    # ASCII
                if uni>31:                                   # 可显示字符 
                    addr = asc_addr + uni*asc_size                
                    self.flash.readinto(addr, asc_buf)
                    yield asc_w, h, asc_buf                  # 返回字模数据的像素宽度、高度、缓存                
                elif uni==10: yield LF_WIDTH, h, asc_buf     # 换行符
                elif uni==13: yield CR_WIDTH, h, asc_buf     # 回车符
            else:                                            # GB2312
                gb_code = self.gb2312(uni)
                addr = gb_addr + ((gb_code[0]-0xA1)*94+gb_code[1]-0xA1)*gb_size                
                self.flash.readinto(addr, gb_buf)
                yield gb_w, h, gb_buf                        # 返回字模数据的像素宽度、高度、缓存
                
if __name__ == "__main__":
    from machine import SPI,Pin
    # 4M闪存（ST7789V显示模块自带字库芯片）
    file_path = '/sd/font_12-32_map_dir.bin'
    lcd_cs = Pin(21,mode=Pin.OUT, value=1)
    spi = SPI(2, 10_000_000, sck=0, mosi=4, miso=5)  
   
    # 写入字库文件   
#     fw = BurnFlash(spi, 22)    
#     fw.write(file_path,erase=True)

    str_test = '测試𠀀\nTEST'                                # 测试字符串（試和𠀀不是GB2312字符）
    font = Font(spi, 22)
    print(font)                                              # 打印font对象（调用__str__()）

    for h in font.pixel_h():                                 # 遍历字模文件中所有的像素高度 
        asc_buf = bytearray(font.size(h,True))               # 定义读取ASCII字模的缓存 
        gb_buf = bytearray(font.size(h,False))               # 定义读取GB2312字模的缓存
        for w,h,data in font.read(str_test,h):               # 使用read()生成器读取
            print(w,h,'→',data.hex(' '))                     # 打印结果
        for w,h,data in font.readinto(str_test,h,asc_buf=asc_buf, gb_buf=gb_buf):
            print(w,h,'→',data.hex(' ')) 
