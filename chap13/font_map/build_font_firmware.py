import argparse
import struct

def build_font_firmware(font_bin, font_py):        
    with open(font_bin, 'rb') as f:                     # 打开字库文件
        _desc = {}
        header = f.read(16)                             # 读取文件基础头(16字节) 
        d = struct.unpack('>4sHIHI', header)            # 解包文件头
        # 解包结果：魔数、字模描述项数量、字模描述表地址、是否分段索引GB2312编码、GB2312编码地址
        magic, desc_count, desc_addr, _seg_idx, _BASE1 = d 
        if magic != b'FONT': raise ValueError("无效字库文件（魔数不匹配）") 
        # 初始化分段索引GB2312编码的各段地址(无论使用哪种索引，都要创建，以填充驱动程序)
        _BASE2 = _BASE1+(0x0451-0x0000+1)*2
        _BASE3 = _BASE2+(0x2642-0x2015+1)*2
        _BASE4 = _BASE3+(0x3229-0x3000+1)*2
        _BASE5 = _BASE4+(0x9FA0-0x4E00+1)*2
                    
        f.seek(desc_addr)                               # 定位到字模描述表
        for i in range(desc_count):                     # 遍历所有描述表
            desc_data = f.read(12)                      # 读取一种字模集的描述项（12字节）
            # 字模集信息：字符集(1是ASCII,2是GB2312)、像素宽、像素高、单字模字节长度、字模偏移地址
            charset, w, h, size, addr = struct.unpack('>4HI', desc_data)
            v = _desc.get(h,None)                       # 以h为键，查询值
            if v is None: v = _desc[h] = {}             # 添加键值对（值也是字典对象）
            if charset==1: v['asc_w']=w; v['asc_size']=size; v['asc_addr']=addr
            else:          v['gb_w']=w;  v['gb_size']=size;  v['gb_addr']=addr
        
        f.seek(0)                                       # 定位到文件头
        FONT_BIN = f.read()                             # 读取全部数据
        py_code = f"""
from micropython import const
FONT_BIN = {FONT_BIN}
class Font:                                                 # 固件字库驱动类 
    _instance = None
    LF_WIDTH  = const(-1)                                   # 特殊标记：换行符Line Feed的宽度
    CR_WIDTH  = const(-2)                                   # 特殊标记：回车符Carriage Return的宽度
    
    def __new__(cls, *args, **kwargs):                      # 限制该类只能创建单例对象
        if cls._instance is None: cls._instance = super().__new__(cls) 
        return cls._instance   

    def __init__(self):
        self._desc = {_desc}
        self._seg_idx = {_seg_idx}
        self._BASE1 = {_BASE1}
        if self._seg_idx:            
            self._BASE2 = {_BASE2}
            self._BASE3 = {_BASE3}
            self._BASE4 = {_BASE4}
            self._BASE5 = {_BASE5}
        
    def __str__(self):                                      # 返回字模信息字符串（如asc6x12/gb12x12)
        sorted_items = sorted(self._desc.items())           # 取得按键排序的元组
        buf = bytearray() 
        for h, d in sorted_items:                           # 遍历元组所有数据项
            buf.extend(f'asc{{d[\"asc_w\"]}}x{{h}}\\ngb{{d[\"gb_w\"]}}x{{h}}\\n'.encode()) # 添加字模集信息，如asc6x12、gb12x12
        return buf.decode()
            
    def gb2312(self, uni):                                   # 返回Unicode码位uni的gb2312编码        
        if self._seg_idx:                                    # 用Unicode码位分段索引
            if uni<=0x0451:           addr = self._BASE1+uni*2
            elif 0x2015<=uni<=0x2642: addr = self._BASE2+(uni-0x2015)*2
            elif 0x3000<=uni<=0x3229: addr = self._BASE3+(uni-0x3000)*2
            elif 0x4E00<=uni<=0x9FA0: addr = self._BASE4+(uni-0x4E00)*2
            elif 0xFF01<=uni<=0xFFE5: addr = self._BASE5+(uni-0xFF01)*2
            else: addr=self._BASE1
        else:                                               # 用Unicode码位直接索引
            if uni>0xFFE5: addr=self._BASE1                 # GB2312编码的起始地址
            else:          addr=self._BASE1+uni*2           # _BASE1是GB2312编码的起始地址        
        gb_bytes = FONT_BIN[addr:addr+2]
        if gb_bytes[0]>0xFE or gb_bytes[0]==0:              # 无法识别字符返回的GB2312编码是0xFFFF或0x0
            gb_bytes=b'\\xA1\\xA1'                          # 用全角空格代替无法识别字符
        return gb_bytes
     
    def pixel_h(self):                                       # 返回文件中所有字模集的像素高度（元组）
        return (self._desc.keys())
        
    def size(self, h, asc = True):                        # 返回像素高度为h单个字模的字节长度
        v = self._desc.get(h,None)
        if v: return v.get('asc_size',0) if asc else v.get('gb_size',0)
        else: return 0
   
    def read(self, s, h):
        v = self._desc.get(h,None)
        if v is None: raise ValueError(f'字库不包含像素高度为{{h}}的字模')
        asc_w=v['asc_w']; asc_size=v['asc_size']; asc_addr=v['asc_addr']
        gb_w=v['gb_w'];   gb_size=v['gb_size'];   gb_addr=v['gb_addr']        
        for c in s:                                          # 遍历字符串s
            uni = ord(c)
            if uni < 127:                                    # ASCII 
                addr = asc_addr + uni*asc_size                
                yield asc_w,h, FONT_BIN[addr:addr+asc_size]
            if uni < 127:                                    # ASCII (127是删除键)
                if uni>31:                                   # 可显示字符 
                    addr = asc_addr + uni*asc_size
                    yield asc_w,h, FONT_BIN[addr:addr+asc_size]
                elif uni==10: yield LF_WIDTH, h, b''         # 换行符
                elif uni==13: yield CR_WIDTH, h, b''         # 回车符    
            else:                                            # GB2312
                gb_code = self.gb2312(uni)
                addr = gb_addr + ((gb_code[0]-0xA1)*94+gb_code[1]-0xA1)*gb_size                
                yield gb_w,h, FONT_BIN[addr:addr+gb_size]     # 返回字符对应的像素宽度、高度、字模
                
    def readinto(self, s, h, *, asc_buf=None, gb_buf=None):
        return self.read(s,h)    

if __name__ == '__main__':
    str_test = '测試𠀀TES'                                    # 测试字符串
    font = Font()
    print(font)                                              # 打印font对象（调用__str__()）
    for h in font.pixel_h():                                 # 遍历所有高度的字模
        for w,h,data in font.read(str_test,h):               # 使用read()生成器读取
            print(w,h,'→',data.hex(' '))                     # 打印结果
"""
        with open(font_py,'w',encoding='utf-8') as fpy:                  # 打开脚本文件准备写入
            fpy.write(py_code) 
    
def main():
    parser = argparse.ArgumentParser(description='生成冻结到固件的字模驱动脚本')    
    parser.add_argument('-f', '--font', required=True, help='最终字模文件（如font_small.bin）')
    parser.add_argument('-o', '--output', default='font_firmware.py', help='输出文件名(默认font_firmware.py)')
    args = parser.parse_args()
    
    build_font_firmware(args.font, args.output)
    print(f"成功生成文件{args.output}")
    
if __name__ == '__main__':
    main()
    # 运行参数-f font_12_map_seg.bin -o font_firmware.py