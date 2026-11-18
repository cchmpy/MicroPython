import struct
from esp32 import Partition
from esp import flash_read
from gc import collect
from sys import exit,print_exception
from micropython import const

class BurnPartition:
    def __init__(self,partition_name):
        try:
            self._p=Partition(partition_name)                    # 获取保存字模数据的分区对象            
            bs = self._p.ioctl(5,0)                              # 获取块大小:4096字节
            self._block_size = bs if bs else 512                 # 若iotcl()返回None，则使用默认值512
            self._blocks = self._p.ioctl(4,0)                    # 分区总块数
            _,_,self._BASE0,self._psize,*_  = self._p.info()     # 分区起始地址、分区大小
            self._buf = memoryview(bytearray(self._block_size))  # 读写缓冲（大小与分区块相同）            
        except OSError as e: 
            print_exception(e)
            exit(0)                                              # 退出并软重置系统
    
    def _erase(self):                                            # 擦除目标分区
        b = self._blocks; p = self._p
        print('  擦除目标分区，已完成：')
        for i in range(b):
            p.ioctl(6,i)                                         # 擦除第i块
            print(f'  {(i+1)*100//b}%\r',end='')                 # 打印擦除进度
        print('\n√ 完成擦除')
        
    def write(self, font_file):                                  # 写入二进制字模文件
        # secotor: 从本分区的第几个扇区开始写入
        bs = self._block_size; buf = self._buf                   # 缓存实例变量        
        # 1、打开文件、检查文件和分区大小、擦除分区
        try: f = open(font_file,'rb')
        except OSError:
            print(f'× 无法打开字模文件,它可能不存在')
            return None
        fsize = f.seek(0,2)                                      # 固件文件总大小
        f.seek(0)                                                # 定位到文件开头
        if fsize > self._psize:                                  # 检查分区大小是否满足要求
            print(f'× 字模文件大小[{fsize}]超过分区容量[{self._psize}]，无法写入')
            return None
        self._erase()                                            # 擦除分区
    
        # 2、将文件写入分区
        print('  写入字模文件...')        
        block_id = 0                                             # 待写入分区块编号（分区的第一个扇区）
        t = 0                                                    # 写入分区总字节书
        while size := f.readinto(buf):                           # 读取固件
            if size != bs: buf = buf[:size]                      # 读取到文件末尾
            self._p.writeblocks(block_id,buf,0)                  # 写入块
            block_id += 1                                        # 下一个块
            t += size                                            # 更新写入总字节数
            print(f'  {t*100//fsize}%\r',end='')                 # 打印写入进度
        print('\n√ 完成写入')
        f.close()                                                # 关闭文件
# ----------------------------------------------------------------------------------------       
class Font:                                            # 字库驱动类（分区存储）
    _partition_font = {}                                        # 键:分区名，值:Font对象
    _first_init = True
    LF_WIDTH    = const(-1)                                     # 特殊标记：换行符Line Feed的宽度
    CR_WIDTH    = const(-2)                                     # 特殊标记：回车符Carriage Return的宽度    
    
    def __new__(cls, partition_name, *args, **kwargs):          # 同一个分区只能创建一个对象
        if partition_name not in cls._partition_font.keys():    # 该分区上没有创建过Font对象
            cls._first_init = True
            cls._partition_font[partition_name] = super().__new__(cls)
        return cls._partition_font[partition_name]
    
    def __init__(self, partition_name):                         # font_path：字库文件路径
        if self._first_init:
            self._first_init = False
            self._gb_buf = bytearray(2)                         # 保存GB2312编码的缓冲
            self._p=Partition(partition_name)                   # 获取保存字模数据的分区对象
            _,_,self._BASE0,*_ = self._p.info()                 # 分区起始地址        
            # _desc格式：{h:{asc_w:w, asc_size:size, asc_addr:addr, gb_w:w, gb_size:size, gb_addr:addr}}
            self._desc = {}                                     # 描述所有字模集信息的字典
            buf16 = bytearray(16)
            buf12 = bytearray(12)
            flash_read(self._BASE0,buf16)                       # 读取文件基础头(16字节) 
            d = struct.unpack('>4sHIHI', buf16)                 # 解包文件头
            # 解包结果：魔数、字模描述项数量、字模描述表地址、是否分段索引GB2312编码、GB2312编码地址
            magic, desc_count, desc_addr, self._seg_idx, self._BASE1 = d
            desc_addr += self._BASE0                            # 计算字模描述表在闪存中的绝对地址
            self._BASE1 += self._BASE0                          # 计算GB2312编码在闪存中的绝对地址
            if magic != b'FONT': raise ValueError("无效字库文件（魔数不匹配）")            
            if self._seg_idx:                                   # 初始化分段索引GB2312编码的各段地址
                self._BASE2 = self._BASE1+(0x0451-0x0000+1)*2
                self._BASE3 = self._BASE2+(0x2642-0x2015+1)*2
                self._BASE4 = self._BASE3+(0x3229-0x3000+1)*2
                self._BASE5 = self._BASE4+(0x9FA0-0x4E00+1)*2
             
            for i in range(desc_count):                         # 遍历所有描述表
                flash_read(desc_addr,buf12)                     # 读取一种字模集的描述项（12字节）
                # 解包该字模集信息：字符集(1是ASCII,2是GB2312)、像素宽、像素高、单字模字节长度、字模偏移地址
                charset, w, h, size, addr = struct.unpack('>4HI', buf12)
                v = self._desc.get(h,None)                      # 以h为键，查询值
                if v is None: v = self._desc[h] = {}            # 添加键值对（值也是字典对象）
                if charset==1: v['asc_w']=w; v['asc_size']=size; v['asc_addr']=addr+self._BASE0
                else:          v['gb_w']=w;  v['gb_size']=size;  v['gb_addr']=addr+self._BASE0
                desc_addr += 12                                 # 下一个描述项的地址
            del buf12
            del buf16
            collect()                                           # 手动执行垃圾收集
        
    def __str__(self):                                          # 返回字模信息字符串（如asc6x12/gb12x12)
        sorted_items = sorted(self._desc.items())               # 取得按键排序的元组
        buf = bytearray() 
        for h, d in sorted_items:                               # 遍历元组所有数据项
            buf.extend(f'asc{d["asc_w"]}x{h}\ngb{d["gb_w"]}x{h}\n') # 添加字模集信息，如asc6x12、gb12x12
        return buf.decode()
    
    def gb2312(self, uni):                                      # 返回Unicode码位uni的gb2312编码
        if self._seg_idx:                                       # 用Unicode码位分段索引
            if uni<=0x0451:           addr = self._BASE1+uni*2
            elif 0x2015<=uni<=0x2642: addr = self._BASE2+(uni-0x2015)*2
            elif 0x3000<=uni<=0x3229: addr = self._BASE3+(uni-0x3000)*2
            elif 0x4E00<=uni<=0x9FA0: addr = self._BASE4+(uni-0x4E00)*2
            elif 0xFF01<=uni<=0xFFE5: addr = self._BASE5+(uni-0xFF01)*2
            else: addr=self._BASE1                              # uni是空码位或超越索引范围，地址设为空码位
        else:                                                   # 用Unicode码位直接索引
            if uni>0xFFE5: addr=self._BASE1                     # uni超出索引, 地址设为GB2312的空码位
            else:          addr=self._BASE1+uni*2               # _BASE1是GB2312编码的起始地址 
        buf = self._gb_buf
        flash_read(addr, buf)                                   # 读取GB2312编码到缓冲区（2字节）        
        if buf[0]>0xFE or buf[0]==0:                            # 无法识别字符返回的GB2312编码是0xFFFF或0x0
            buf[0]=buf[1]=0xA1                                  # 用全角空格代替无法识别字符
        return buf 
    
    def pixel_h(self):                                           # 返回文件中所有字模集的像素高度（元组）
        return (self._desc.keys())
        
    def size(self, h, asc = True):                               # 返回像素高度为h单个字模的字节长度
        v = self._desc.get(h,None)
        if v: return v.get('asc_size',0) if asc else v.get('gb_size',0)
        else: return 0
    
    def read(self,s,h):
        return self.readinto(s,h,asc_buf=None, gb_buf=None)
        
    def readinto(self, s, h, *, asc_buf=None, gb_buf=None):
        v = self._desc.get(h,None)
        if v is None: raise ValueError(f'字库不包含像素高度为{h}的字模')
        asc_w=v['asc_w']; asc_size=v['asc_size']; asc_addr=v['asc_addr']
        gb_w=v['gb_w'];   gb_size=v['gb_size'];   gb_addr=v['gb_addr']
        if asc_buf is None: asc_buf = bytearray(asc_size)
        if gb_buf is None:  gb_buf = bytearray(gb_size) 
        for c in s:                                              # 遍历字符串
            uni = ord(c)
            if uni < 127:                                        # ASCII   
                if uni>31:                                       # 可显示字符 
                    addr = asc_addr + uni*asc_size
                    flash_read(addr, asc_buf)
                    yield asc_w, h, asc_buf                      # 返回字模数据的像素宽度、高度、缓存
                elif uni==10: yield LF_WIDTH, h, asc_buf         # 换行符
                elif uni==13: yield CR_WIDTH, h, asc_buf         # 回车符
            else:                                                # GB2312
                gb_code = self.gb2312(uni)
                addr = gb_addr + ((gb_code[0]-0xA1)*94+gb_code[1]-0xA1)*gb_size
                flash_read(addr, gb_buf)
                yield gb_w, h, gb_buf                            # 返回字模数据的像素宽度、高度、缓存         
 
if __name__ == '__main__':
    # 首次测试，把索引式字库写入闪存分区，分区名user_data
#     burn = BurnPartition('user_data')
#     burn.write('font_12_map_dir.bin')                          # 向目标分区写入字库文件
    str_test = '测試𠀀\nTEST'                                    # 测试字符串（試和𠀀不是GB2312字符）     
    font = Font('user_data')
    print(font)                                                  # 打印font对象（调用__str__()）
    for h in font.pixel_h():                                     # 遍历字模文件中所有的像素高度 
        asc_buf = bytearray(font.size(h,True))                   # 定义读取ASCII字模的缓存 
        gb_buf = bytearray(font.size(h,False))                   # 定义读取GB2312字模的缓存        
        for w,h,data in font.readinto(str_test,h,asc_buf=asc_buf, gb_buf=gb_buf):
            print(w,h,'→',data.hex(' '))
    
