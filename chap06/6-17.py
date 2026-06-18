import uctypes
from struct import pack
class Bitmap:
    # BMP文件头和信息头结构描述符（共54字节，信息头是标准40字节版本）
    BMP_HEADER_DESC = {
        'type':      0 | uctypes.UINT16,        # 文件类型：BM
        'size':      2 | uctypes.UINT32,        # 文件总大小（字节）
        'reserved1': 6 | uctypes.UINT16,        # 保留
        'reserved2': 8 | uctypes.UINT16,        # 保留
        'offset':   10 | uctypes.UINT32,        # 图像本身的起始偏移量
   
        'info_size':  14 | uctypes.UINT32,      # 信息头大小
        'w':          18 | uctypes.INT32,       # 图像宽度（像素数),可以为负数
        'h':          22 | uctypes.INT32,       # 图像高度（像素数),负值表示按行从上到下存储
        'planes':     26 | uctypes.UINT16,      # 颜色平面数（始终为1）
        'bits_pixel': 28 | uctypes.UINT16,      # 每像素的位数（1,4,8,16,24,32）
        'compression':30 | uctypes.UINT32,      # 压缩方式（0表示无压缩）
        'size_img':   34 | uctypes.UINT32,      # 图像本身的数据大小（字节数）
        'x_pixels':   38 | uctypes.INT32,       # 水平分辨率（像素/米）
        'y_pixels':   42 | uctypes.INT32,       # 垂直分辨率（像素/米）
        'clr_used':   46 | uctypes.UINT32,      # 调色板颜色数
        'clr_impt':   50 | uctypes.UINT32,      # 重要颜色数（0表示全部重要）
    } 
    # 定义一个RGB565格式像素的位域结构描述符 RGB565 = 0xRRRR RGGG GGGB BBBB
    RGB565_DESC = {'r':0 | uctypes.BFUINT16 | 11<<uctypes.BF_POS | 5<<uctypes.BF_LEN,
                   'g':0 | uctypes.BFUINT16 | 5 <<uctypes.BF_POS | 6<<uctypes.BF_LEN,
                   'b':0 | uctypes.BFUINT16 | 0 <<uctypes.BF_POS | 5<<uctypes.BF_LEN,}
    
    def __init__(self, bmp_file): 
        self.bmp = open(bmp_file,'rb')          # 打开图像文件 
        self._parse_header()                    # 解析文件头，定义self.header实例变量
   
    def close(self):                            # 关闭文件  
        try: self.bmp.close()
        except: pass

    def _parse_header(self):
        header_data = self.bmp.read(54)
        addr = uctypes.addressof(header_data)
        self.header = uctypes.struct(addr,self.BMP_HEADER_DESC,uctypes.LITTLE_ENDIAN)
        if self.header.type != 0x4D42:
            self.close()
            raise('Not a valid BMP file')  # 验证文件类型：'BM' 
        
    def bmp2432_to_16(self, target, byteorder=uctypes.LITTLE_ENDIAN):    # 24/32位bmp图像转换为16位
        header = self.header
        if header.bits_pixel not in (24,32):
            print('A pixels of BMP should be 24 bits or 32 bits.')
            return None
        b2432 = (abs(header.w)*header.bits_pixel+31)//32*4       # bmp2432文件每行字节数（4的倍数） 
        b16   = (abs(header.w) * 16 + 31) // 32 * 4              # bmp16每行字节数 
        buf2432, buf16 = bytearray(b2432), bytearray(b16)        # 读写缓存（都是1行）
 
        self.bmp.seek(header.offset)                             # 定位到图像数据的位置
        with open(target,'wb') as f16: 
            offset, img_size = 14+40+16, b16*abs(header.h)       # bmp16图像数据偏移位置和大小
            # 分别写入文件头、信息头、RGB565掩码
            f16.write(pack('<HIHHI',0x4D42,offset+img_size,0,0,offset))
            f16.write(pack('<IiiHHIIiiII',40,header.w, header.h,1,16,3,img_size,0,0,0,0))
            f16.write(pack('<4I',0xF800,0x07E0,0x001F,0)) 
            ARR_DESC = (uctypes.ARRAY, b16//2, self.RGB565_DESC) # 一行rgb565像素的位域类型数组的描述符
            a = uctypes.struct(uctypes.addressof(buf16),ARR_DESC,byteorder) # 一行rgb565像素的数组结构体
            while self.bmp.readinto(buf2432):                    # 读取bmp2432的一行像素，逐行操作
                i = 0                                            # bmp16一行像素对应数组下标(第几个像素)
                for j in range(0,b2432,header.bits_pixel//8):    # 逐个处理像素,j是bmp2432的第几个像素
                    a[i].b = buf2432[j]>>3                       # bmp图像按BGR顺序存储像素颜色
                    a[i].g = buf2432[j+1]>>2
                    a[i].r = buf2432[j+2]>>3
                    i+=1 
                f16.write(buf16)                                 # 向bmp16文件写入1行像素
    
    def __enter__(self): return self                             # 上下文协议，入口函数 
    def __exit__(self,*args):self.close()                        # 上下文协议，出口函数 
    
    def __str__(self):
        header = self.header
        return f'''BMP File Header:
type: {header.type.to_bytes(2,'little')}
size: {header.size}
offset: {header.offset}\n
BMP Info Header:
head size: {header.info_size}
image size: {abs(header.w)} x {abs(header.h)}
bits_per_pixel: {header.bits_pixel}
compression: {header.compression}
image size: {header.size_img}
'''     
if __name__ == '__main__':
    with Bitmap('img24.bmp') as f:
        print(f)
        f.bmp2432_to_16('16.bmp')
