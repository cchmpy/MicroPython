from micropython import const
import framebuf, font16x16

# 用于初始化的寄存器命令,按手册建议的先后顺序罗列
_SET_MUX_RATIO    = const(0xA8)     # 双字节指令:设置复用率即选通的COM行数
_SET_DISP_OFF_SET = const(0xD3)     # 双字节:设置偏移量,屏幕向上移动行数
_SET_DISP_START_LINE = const(0x40)  # 单字节,设置显存第几行映射到com0,0x40|(0~63)
_SET_SEG_REMAP   = const(0xA0)  # 单字节:左右反转,设置显存第0(0xA0)或127(0xA1)列映射到SEG0
_SET_COM_OUT_DIR = const(0xC0)  # 单字节:上下反转,COM扫描方向,0xC0从COM0扫描到COM[N-1],0xC8反之
_SET_COM_PIN_CFG = const(0xDA)  # 双字节:设置COM引脚硬件配置,匹配面板布线
_SET_CONTRAST    = const(0x81)  # 双字节:设置对比度,默认0x7f
_SET_ENTIRE_ON   = const(0xA4)  # 单字节:设置正常显示显存数据,0xA5全屏点亮
_SET_NORM_INV    = const(0xA6)  # 单字节:设置正常(1亮0灭),反转0xA7
_SET_MEM_ADDR    = const(0x20)  # 双字节:设置显存寻址模式,参数:0-水平,1-垂直,2-页
_SET_DISP_CLK_DIV= const(0xD5)  # 双字节:设置显示时钟分频数和fosc,默认80h

_SET_VCOM_DESEL  = const(0xDB)  # 双字节:设置VCOMH输出的高电平,0x00-0.65*Vcc,0x10-0.77*Vcc,0x30-0.83*Vcc
_SET_PRECHARGE   = const(0xD9)  # 双字节:设置充放电持续时间(DCLK数),默认值0x22。
_SET_CHARGE_PUMP = const(0x8D)  # 双字节:是否启用电荷泵调节电路。0x10禁用,0x14启用。
_SET_DISP        = const(0xAE)  # 设置显示关0xAE(默认),显示开0xAF

# 其它命令
_SET_COL_ADDR    = const(0x21)  # 三字节:设置水平/垂直模式的初始列和结束列,00H~7FH 
_SET_PAGE_ADDR   = const(0x22)  # 三字节:设置水平/垂直模式的初始页和结束页, 0~7

class SSD1306_I2C(framebuf.FrameBuffer):
    def __init__(self,i2c, width=128, height=64, addr=0x3c, font=None,external_vcc=False):
        # font: 是一个font16x16.File对象实例，如果不为None则优先使用它读取点阵数据，
# 否则使用font16x16.Flash读取
        self._w     = width
        self._h     = height
        self._font  = font if font else font16x16.Flash() # 选择读取字符点阵数据的对象
        self._pages = height>>3       # 显示屏页数
        self._i2c   = i2c
        self._addr  = addr            # 设备从机地址
        
        self._ext_vcc = external_vcc  # 芯片VCC引脚是否接入外部电源        
        self._cbuf    = bytearray(2)  # 发送指令的缓存,首字节为控制字节
        self._cbuf[0] = 0x80          # Co=1(bit7)后面是命令, D/C#=0(bit6)下个字节是命令
        self._dbuf    = memoryview(bytearray(self._w*self._pages+1)) # 多一个控制字节（首字节）
        self._dbuf[0] = 0x40          # Co=0(bit7)后面是数据, D/C#=1(bit6)下个字节是数据
        self._part    = [b'\x40']     # 用于部分刷新，避免额外内存分配
        self._p0,self._p1 = 0,0       # 部分刷新时的起止页 
        super().__init__(self._dbuf[1:], self._w, self._h, framebuf.MONO_VLSB) # 初始化基类
        
        # 初始化寄存器
        for cmd in (
            _SET_MUX_RATIO,height-1,  # 设置复用率即选通的COM行数(参数+1)
            _SET_DISP_OFF_SET, 0,     # 设置显示偏移，reset=0
            _SET_DISP_START_LINE,     # 设置显存起始行为0,reset=0
            _SET_SEG_REMAP|0x01,      # 设置SEG映射关系，显存第127列映射到SEG0,左右反转
            _SET_COM_OUT_DIR | 0x08,  # 设置com输出扫描方向，从COM64到COM0,上下反转
            _SET_COM_PIN_CFG, 0x02 if self._h == 32 else 0x12, # 128x64奇偶布线,128x32序列布线
            
            _SET_CONTRAST,0x7F,       # 设置显示对比度，使用默认值
            _SET_ENTIRE_ON,           # 正常显示内存数据，而不是全亮
            _SET_NORM_INV,            # 正常显示1亮0灭，不反转
            _SET_MEM_ADDR, 0x0,       # 显存寻址模式:水平寻址
            
            _SET_DISP_CLK_DIV,0xF0,   # 设置显示时钟分频数和fosc,高4位越大,帧率越大,默认80h
            _SET_PRECHARGE,0x22,      # 设置充放电周期，使用默认值
            _SET_VCOM_DESEL,0x30,     # 设置VCOMH输出的高电平0.83*Vcc         
            
            _SET_CHARGE_PUMP, 0x10 if self._ext_vcc else 0x14, # 使能电荷泵调节器
            _SET_DISP | 0x01,         # 开启显示
        ):
            self._write_cmd(cmd)        
        self.clear()              
    
    def _write_cmd(self, cmd):        # 向SSD1306写入命令        
        self._cbuf[1]=cmd
        self._i2c.writeto(self._addr,self._cbuf)
        
    def _write_data(self):            # 向SSD1306写入缓存的全部数据
        self._i2c.writeto(self._addr,self._dbuf)
        
    def _set_window(self,x0,x1,p0,p1):  # 设置显示窗口,列和页的起止地址
        self._write_cmd(_SET_COL_ADDR)
        self._write_cmd(x0)
        self._write_cmd(x1)
        self._write_cmd(_SET_PAGE_ADDR)
        self._write_cmd(p0)
        self._write_cmd(p1)
    
    def clear(self):                   # 清空显示        
        self.fill(0)                   # 调用FrameBuffer.fill()
        self.show()      
    
    def power(self,on=True):           # 开启或关闭显示      
        self._write_cmd(_SET_DISP | on)
    
    def contrast(self, contrast=0x80): # 设置对比度        
        self._write_cmd(_SET_CONTRAST) # 命令
        self._write_cmd(contrast)      # 参数
    
    def invert(self, invert=False):    # 设置颜色反转显示(1亮0灭还是反之) 
        self._write_cmd(_SET_NORM_INV | invert)
    
    def rotate(self, rotate=True):     # 屏幕翻转180°        
        self._write_cmd(_SET_COM_OUT_DIR | ((rotate & 1) << 3))
        self._write_cmd(_SET_SEG_REMAP | (rotate & 1))    
       
    def text_gb16x16(self,s,x,y,offset=0,autowrap=True,alpha=True):
        # 从framebuf的左上角(x,y)处绘制GB2312_16X16字符,autowrap:是否自动换行,
        # alpha:背景是否透明;offset:若从文件读取,值为0,若从flash中读取,则是字模数据的起始地址
        for ch in s:
            if ch=='\n':                           # 响应换行符,无论autowrap是何值
                x,y = 0,y+16                       # 向下移动16个像素
            elif ch=='\r':                         # 响应回车符
                x = 0                              # 移动至行首,y不变
            else:
                d = self._font.read(ch,offset)     # 取得字符的宽、高、点阵数据 
                if x+d[0]>self._w:                 # 超出屏幕右侧
                    if autowrap:    x,y = 0,y+d[1] # 如果自动换行，则换到下一行开头                                                 
                    else:           continue       # 否则继续遍历文本,寻找回车换行
                if y+d[1]>self._h:  return         # 超出屏幕下边缘            
                fbuf=framebuf.FrameBuffer(d[2],d[0],d[1],framebuf.MONO_HLSB) # 定义字体的framebuffer
                self.blit(fbuf,x,y,0 if alpha else -1)                       # 在framebuf上绘制汉字                 
                x+=d[0]                            # 向右移动一个字符的位置 
    
    def show(self):               # 全屏显示刷新，把FrameBuffer的全部数据发送到屏幕 
        self._set_window(0,self._w-1,0,self._pages-1)
        self._write_data() 
   
    def part_data(self,x,y,w,h):  # 定义部分显示刷新的矩形区域 
        del self._part[1:]                          # 删除原有数据
        self._p0,self._p1=y//8,(y+h-1)//8           # 开始、结束页 
        for i in range(self._p0,self._p1+1):        # 遍历所有页
            st = 1+self._w*i+x                      # 本页需显示像素开始的位置
            self._part.append(self._dbuf[st:st+w])  # 将本页的切片数据加入列表
            
    def part_show(self,x,y,w,h):  # 部分显示刷新 
        self._set_window(x,x+w-1,self._p0,self._p1) 
        self._i2c.writevto(self._addr,self._part)
    
if __name__=='__main__':
    from machine import I2C,Pin
    import  time
    i2c=I2C(0,scl=Pin(32),sda=Pin(33),freq=400_000) # 最高频率可设1.2MHz
    
    font_in_file = True   # 选择使用哪里的字库,True:文件,False:Flash
    if font_in_file:      # 使用文件中的字符点阵数据
        offset = 0
        fbm=font16x16.File('gb16x16.bin')
        oled=SSD1306_I2C(i2c,font=fbm)
    else:                 # 使用flash中的点阵数据
        offset = 0x380000 # 字库在flash中的偏移地址
        oled=SSD1306_I2S(i2c)
        
    # 待显示文本,txt[0]自动换行,txt[1]使用自动+换行符,txt[3]保留原始字符
    txt=['云母屏风烛影深，长河渐落晓星沉。嫦娥应悔偷灵药，碧海青天夜夜心。',
         '床前看月光，\n疑是地上霜。\n举头望山月，\n低头思故乡。',
         r'小时不识月，\n呼作白玉盘。\n又疑瑶台镜，\n飞在青云端。']    
    for i in range(3):
        oled.fill(0) 
        oled.text_gb16x16(txt[i],0,0,offset,alpha=False)
        oled.show()
        time.sleep(2)    
    
    r = (0,0,63,63)  
    oled.part_data(*r) # 组织局部刷新矩形内的数据
    for x in range(4):
        oled.text_gb16x16(str(x),x*8,x*16,offset,alpha=False)
        oled.part_show(*r) 

    time.sleep(10)
    oled.power(False)
    if font_in_file:
        fbm.deinit() # 关闭字库文件
