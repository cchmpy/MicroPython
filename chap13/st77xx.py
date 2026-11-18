from time import sleep_ms
from struct import pack
from machine import Pin, PWM, SPI
from micropython import const
import framebuf
# ST77xx 通用指令
_SLPIN   = const(0x10)                                     # 睡眠(默认),唤醒:0x11
_MADCTL  = const(0x36)                                     # 显存数据访问控制(MY MX MV ML RGB MH.)
_COLMOD  = const(0x3A)                                     # 接口像素格式(默认RGB666:0x66)
_INVOFF  = const(0x20)                                     # 关闭颜色翻转(默认),开启:0x21
_DISPOFF = const(0x28)                                     # 关闭显示(默认),开启:0x29
_RAMWR   = const(0x2C)                                     # 显存写入,显存读取:0x2E
_CASET   = const(0x2A)                                     # 显示目标窗口的列地址设置
_RASET   = const(0x2B)                                     # 显示目标窗口的行地址设置
_PTLAR   = const(0x30)                                     # 设置局部显示模式的局部区域
_VSCSAD  = const(0x37)                                     # 设置滚动显示模式的垂直滚动起始地址

class FrameBufferRGB(framebuf.FrameBuffer):                # 增加绘制汉字和图像的RGB565格式帧缓冲类
    # 定义RGB565颜色常量（主控小端序、ST77xx大端序）
    WHITE = 0xFFFF; BLACK = 0x0; GREY = 0x1084; RED = 0x00F8; GREEN = 0xE007 
    BLUE = 0x1F00;  CYAN = 0xFF07; YELLOW = 0xE0FF; PURPLE = 0x1FF8

    @staticmethod
    def rgb565(r,g,b):                                     # 将R、G、B三基色转换成RGB565
        return (b>>3 | (g&0x1C)<<3)<<8 | (r&0xF8 | g>>5) 

    def __init__(self, width, height, font=None): 
        self._w=width; self._h=height; self._font=font
        self.buf = memoryview(bytearray(width*height*2))                       # 绘图缓存 
        self._palette = framebuf.FrameBuffer(bytearray(4),2,1,framebuf.RGB565) # 绘制字符所用调色板
        super().__init__(self.buf, self._w, self._h, framebuf.RGB565)          # 基类初始化 
    
    def buf_reshape(self):                                 # 改变缓存形状（宽高交换），旋转屏幕时用
        self._w, self._h = self._h, self._w
        super().__init__(self.buf, self._w, self._h, framebuf.RGB565)
        
    def text_gb2312(self, s, x, y, font_clr=0xFFFF, bg_clr=0, font_h=16,
                    alpha=False, autowrap=False, asc_buf=None, gb_buf=None,line_spacing=4):
        if self._font is None: return                      # 字库对象 
        self._palette.pixel(0,0,bg_clr)                    # 把背景色写入rgb565格式调色板
        self._palette.pixel(1,0,font_clr)                  # 把前景色写入rgb565格式调色板
        if asc_buf or gb_buf: data = self._font.readinto(s,font_h, asc_buf=asc_buf, gb_buf=gb_buf)
        else:                 data = self._font.read(s, font_h)
        for w, h, bm in data:
            if w == self._font.LF_WIDTH:                   # 遇到换行符(回车被忽略)
                x=0; y=y+h+line_spacing                    # 定位到下一行开头
                continue                                   # 处理下一个字模数据
            elif w== self._font.CR_WIDTH:                  # 回车符,y不变
                x=0; continue                              
            if x+w>self._w:                                # 超出屏幕右侧
                if autowrap: x=0; y=y+h+line_spacing       # 如果自动换行,则换到下一行开头
                else:        break                         # 否则停止绘制
            if y+h>self._h:  break                         # 超出屏幕下边缘不绘制
            fbuf=(bm,w,h,framebuf.MONO_HLSB)               # 定义字体的framebuffer
            self.blit(fbuf,x,y,bg_clr if alpha else -1,self._palette)        # 在帧缓冲上绘制汉字
            x+=w                                           # 下一个字符的x坐标
            
    def image(self,x,y,w,h,image):                         # 在主控帧缓冲上绘制RGB565格式图像 
        if isinstance(image,framebuf.FrameBuffer):         # image是FrameBufferRGB/FrameBuffer
            self.blit(image,x,y)
        else: self.blit((image,w,h,framebuf.RGB565),x,y)   # image是bytearray,bytes,memoryview
        
class ST77xx(FrameBufferRGB):                              # ST77xx通用驱动类（ST7735/ST7789/ST7796)
    # 类变量，显示模式指令,用于方法set_dis_mode(mode,*p)
    DIS_NORMAL = 0x13                                      # 正常模式(默认)
    DIS_PART   = 0x12                                      # 部分显示模式
    DIS_IDLE   = 0x39                                      # 空闲显示模式,关闭:0x38
    DIS_SCROLL = 0x33                                      # 垂直滚动显示模式
    # MADCT(0x36)命令的参数(对应源极线逆序、正序连接下屏幕相对默认值旋转0°、90°、180°、270°）
    _PARA_MADCTL =(b'\x48\x28\x88\xE8',b'\x00\x60\xC0\xA0')
    
    def __init__(self,spi,dc,cs,rst,bl, width=240, height=320,font = None,
                 source_forward=True, clr_inverse=False): 
        super().__init__(width,height,font)                # 基类初始化
        self._spi = spi
        self._dc = Pin(dc, Pin.OUT, value=0)               # dc:LCD数据(1)/命令(0)选择引脚 
        self._rst = Pin(rst,Pin.OUT,value=0)               # rst:LCD重置引脚,当前拉低开始复位
        self._cs = Pin(cs,Pin.OUT,value=1)                 # cs:LCD片选
        self._bl = PWM(Pin(bl), freq=1000, duty_u16=0)     # bl:背光引脚,用pwm控制亮度
 
        # 硬件重置/复位 
        sleep_ms(5)                       # 低电平保持时间在5-9us开始复位,大于9us执行复位
        self._rst(1)                      # 取消复位
        sleep_ms(120)                     # 等待(加载默认设置) 
        self._write(_SLPIN | 1)           # 从默认睡眠模式唤醒
        sleep_ms(120)                     # 等待电源电压和时钟电路的时序稳定,120ms内不能发送_SLPIN命令

        # 设置_MADCTL
        self._source = source_forward     # 驱动芯片与液晶屏源极线的连接顺序（True-正序，False-逆序）
        t = ST77xx._PARA_MADCTL[source_forward]
        self._madctl = (t[1] if self._w>self._h else t[0]).to_bytes(1) # 横屏(宽>高),竖屏(宽<高)
        self._write(_MADCTL, self._madctl)
        
        self._write(_COLMOD, b'\x55')                      # 像素格式设为RGB565
        if clr_inverse: self._write(_INVOFF | 1)           # clr_inverse:是否反转颜色 
        self._write(_DISPOFF | 1)                          # 开启显示 
        self.clear()                                       # 用黑色填充缓存并显示 
        self.backlight(200)                                # 开启背光(范围0-255，添加实例变量_backlight)
            
    def _write(self, cmd, data=None):                      # 写入命令和数据 
        self._cs(0)                                        # 开启片选信号
        self._dc(0); self._spi.write(cmd.to_bytes(1))      # 低电平写命令 
        if data: self._dc(1); self._spi.write(data)        # 高电平写数据
        self._cs(1)                                        # 释放片选信号 
    
    def _set_window(self,x,y,w,h):                         # 设置数据发送的目标窗口
        self._write(_CASET,pack(">HH", x, x+w-1))          # 列起止地址
        self._write(_RASET,pack(">HH", y, y+h-1))          # 行起止地址
        
    def set_dis_mode(self,mode,*p):                        # 设置部分\正常\滚动\空闲显示模式 
        # p[0]:  (PART)部分区域开始地址或(SCROLL)滚动顶部固定区
        # p[1]:  (PART)部分区域结束地址或(SCROLL)中间滚动区
        # p[2]:  (SCROLL)滚动底部固定区;  p[3]: (SCROLL)滚动方向
        if mode==ST77xx.DIS_SCROLL: 
            self._madctl = ((self._madctl[0] & 0xEF) | bool(p[3])<<4).to_bytes(1)   # 修改模式中ML位
            self._write(_MADCTL,self._madctl)              # 写入新模式
            self._write(mode,pack('>HHH',p[0],p[1],p[2]))  # 设置滚动区域
        else:
            self._write(mode)
            if mode==ST77xx.DIS_PART: self._write(_PTLAR,pack(">HH", p[0],p[1]))    # 设置部分显示区域 
    
    def set_scroll_start(self,ys):                         # 设置滚动的开始线 
        self._write(_VSCSAD,pack('>H',ys)) 
    
    def clear(self,c=0):                                   # 用颜色c填充帧缓冲并显示，默认黑色 
        self.fill(c); self.show() 
    
    def backlight(self, duty=None):                        # 获取或设置背光亮度（duty：0-255）
        if duty is None: return self._backlight            # 返回背光亮度
        self._backlight = duty%256
        self._bl.duty_u16(self._backlight*257)             # 设置PWM(背光亮度)

    def power(self, on=True):                              # 电源管理（睡眠或唤醒）
        if on: 
            self._write(_SLPIN | 1)                        # 唤醒指令
            sleep_ms(120)                                  # 等待120ms,期间不能发送SLPIN
            self._write(_DISPOFF | 1)                      # 开启显示
            self.backlight(self._backlight)                # 恢复背光 
        else:
            self._bl.duty_u16(0)                           # 关闭背光 
            self._write(_DISPOFF)                          # 关闭显示
            self._write(_SLPIN)                            # 休眠指令
            sleep_ms(120)                                  # 等待5ms,才能发送其它指令(设120ms)
    
    def deinit(self):  
        self.set_dis_mode(self.DIS_NORMAL)                 # 恢复正常,防止其它模式下退出后重启的闪屏现象
        self.power(False); self._bl.deinit()               # 休眠,关闭PWM输出
        
    def rotate(self,angle=0):                              # 屏幕转动angle角度(90的倍数)
        i = angle//90%4                                    # 相对于默认方向，转动的次数
        if i%2==1: self.buf_reshape()                      # 转动奇数次,长宽总是对调,需调整帧缓冲形状
        t = ST77xx._PARA_MADCTL[self._source]              # 从类变量_PARA_MADCTL中取值
        self._madctl = t[i].to_bytes(1) 
        self._write(_MADCTL, self._madctl)                 # 写入新模式
    
    def image_on_lcd(self,x,y,w,h,image):                  # 把RGB565图像直接发送至显示屏
        # image: FrameBufferRGB, bytearray,bytes,memoryview
        if isinstance(image,FrameBufferRGB):               # image是FrameBufferRGB
            image = image.buf
        self._set_window(x,y,w,h)
        self._write(_RAMWR,image) 
    
    def show(self):                                        # 全屏显示，把帧缓冲全部发送到屏幕
        self._set_window(0,0,self._w,self._h) 
        self._write(_RAMWR,self.buf)                       # 显存写入命令 
    
    def show_y_part(self,y,h):                             # 刷新显示矩形(0,y,width,h)区域 
        self._set_window(0,y,self._w,h)
        self._write(_RAMWR,self.buf[(y*self._w)*2:((y+h)*self._w)*2])   # 切片，会创建memoryview对象 

if __name__=='__main__':                                   # 测试程序
    import time
    from font_file import Font
    font = Font('font_12_map_dir.bin');  font_h = 12       # 使用文件字库
    asc_buf = bytearray(font.size(font_h,True))            # 读取ASCII字模的缓存
    gb_buf = bytearray(font.size(font_h,False))            # 读取汉字字模的缓存 
    
    st77xx = 7789                                          # 可设置7735、7789、7796，对应三种模块
    if st77xx == 7735:                                     # st7735s------------------
        w = 128; h = 160                                   # 屏幕分辨率
        spi = SPI(2, 26_000_000, sck=13, mosi=12, miso=33)                    # SPI接口，根据实际连接修改
        lcd=ST77xx(spi,dc=27,cs=26,rst=14,bl=25,width=w,height=h,font=font,   # 根据实际连接修改
                   source_forward=True, clr_inverse=False )                   # 修改参数，确保显示正确
    elif st77xx == 7789:                                   # st7789v------------------ 
        w = 240; h = 320
        spi = SPI(2, 26_000_000, sck=0, mosi=4, miso=5)        
        font_cs = Pin(22,mode=Pin.OUT,value=1)             # 该模块集成字库芯片，故禁用字库片选 
        lcd=ST77xx(spi,dc=19,cs=21,rst=18,bl=23,width=w,height=h,font=font,
                   source_forward=True, clr_inverse=False )
    elif st77xx == 7796:                                   # st7796u------------------
        w = 320; h = 480
        spi = SPI(1,baudrate=80_000_000, sck=12, mosi=11, miso=13)  # ESP32-S3-WROOM，波特率才设为80MHz
        font_cs = Pin(39,mode=Pin.OUT,value=1)                      # 模块集成了字库芯片，禁用字库片选
        lcd=ST77xx(spi,dc=9,cs=10,rst=14,bl=4,width=w,height=h,font=font,
                   source_forward=False, clr_inverse=True)
    else: raise ValueError('st77xx值错误')
    
    m = min(w,h)                                            # 根据最小值选择插图文件
    if m==320:      pic_file = '插图320x180.ebm'
    elif m==240:    pic_file = '插图240x135.ebm'
    else:           pic_file = '插图128x72.ebm'
    with open(pic_file,'rb') as fb, open('古诗.txt','r') as ft: 
        lcd.image(0,0,m,int(m*0.5625),fb.read())            # 三个插图的长宽比例固定
        lcd.text_gb2312(ft.read(),0,int(m*0.5625)+2,font_clr=lcd.WHITE, bg_clr=0,
                    font_h=font_h, alpha=True, autowrap=True, asc_buf=asc_buf, gb_buf=gb_buf)
    lcd.show()                                              # 显示帧缓冲图像
    
    lcd.set_dis_mode(lcd.DIS_SCROLL,50,h-100,50,0)          # 设置滚动显示模式,顶部和底部固定区为50
    t,i=time.ticks_ms(),50
    while time.ticks_diff(time.ticks_ms(),t)<10000:         # 垂直滚动模式持续10秒
        lcd.set_scroll_start(i)                             # 设置滚动开始线
        i = i+1 if i<h-50 else 50                           # 更改滚动开始线
        time.sleep_ms(30)                                   # 控制滚动速度
    lcd.set_dis_mode(lcd.DIS_NORMAL)                        # 恢复正常显示模式
    try:
        while True:time.sleep(0.2)
    except KeyboardInterrupt: lcd.deinit(); spi.deinit()    # Ctrl+c关闭显示
