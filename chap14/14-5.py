from micropython import const
from time import sleep_us
from machine import Pin
_DATACMD = const(0x40)     # 数据命令：数据读写控制位b1、地址模式控制位b2
_ADDRCMD = const(0xC0)     # 地址命令：0xC0-0xCF
_DISCTRL = const(0x80)     # 显示控制：背光亮度控制位[b2:b0]，显示开关控制位[b3]
_TWAIT_US= const(2)        # 读键命令和读键数据之间的等待时间，至少2us

# 共阴极LED对应的字符位图：0-9, A-Z, blank, -, *
_SEGS=b'\x3F\x06\x5B\x4F\x66\x6D\x7D\x07\x7F\x6F\x77\x7C\x39\x5E\x79\x71\x3D\x76\x06\x1E\x76\x38\x55\x54\x3F\x73\x67\x50\x6D\x78\x3E\x1C\x2A\x76\x6E\x5B'

# 按键1～16对应的（字节,编码),字节是BYTE0-BYTE3。不同模块可能有差异，需测试后填入相应数据
_KEYS = ((0,0x04),(0,0x40),(1,0x04),(1,0x40), (2,0x04),(2,0x40),(3,0x04),(3,0x40),
      (0,0x02),(0,0x20),(1,0x02),(1,0x20), (2,0x02),(2,0x20),(3,0x02),(3,0x20))

class TM1638:
    def __init__(self, segs, *, DIO, CLK, STB, comm_anode=False):
        self._segs= segs                               # 数码管位数，共阴极/共阳极LED最多8个和10个
        self._DIO = Pin(DIO,Pin.OUT,Pin.PULL_UP)
        self._CLK = Pin(CLK,Pin.OUT,Pin.PULL_UP)
        self._STB = Pin(STB,Pin.OUT,Pin.PULL_UP,value=1)
        self._comm_anode = comm_anode                  # 是否为共阳极数码管 
        # 显示缓存,前16字节保存原始数据对应的共阴极位图，后16字节是转化为共阳极所用的位图
        # 第一个8字节（前8个LED）转换到第三个8字节, 第二个8字节转化到第四个8字节
        self._buf=bytearray(16*2)                      # 默认值为0
        self._key=bytearray(4)                         # 保存按键信息
        self.brightness(7)                             # 打开电源并设置亮度
    
    def _write_byte(self,b):                           # 写入一个字节到TM1638
        for i in range(8):
            self._CLK(0)                               # CLK低电平时，可以改变DIO信号
            self._DIO(b & 0x01)                        # 改变DIO,输入b[i]位信息
            b>>=1                                      # 左移一位
            self._CLK(1)                               # 在CLK的上升沿，传输DIO信号 
    
    def _read_byte(self,n):                            # 从TM1638读取键扫数据的一个字节到缓存_key[n]'
        self._key[n]=0
        for i in range(8):
            self._CLK(0)                               # CLK低电平时，改变DIO信号
            if self._DIO(): self._key[n] |= 1<<i       # 检查DIO引脚的值（需提前变为输入模式）
            self._CLK(1)                               # CLK上升沿时，读取DIO信号 
    
    def _write_cmd(self,cmd:int):                      # 写入一个命令
        self._STB(0)                                   # 开启片选
        self._write_byte(cmd) 
        self._STB(1)                                   # 关闭片选
    
    def _write_buf(self):                              # 以自增模式把缓存数据写入TM1638
        self._STB(0)                                   # 开启片选
        self._write_byte(_ADDRCMD)                     # 写入地址命令：0xc0
        k,j= (8,1) if self._comm_anode else (self._segs,0)
        for i in range(k):
            self._write_byte(self._buf[i+j*16])        # 把缓存写入c0/c2/c4...ce
            self._write_byte(self._buf[i+8+j*16])      # 写入c1/c3/c5...cf(它们可能没有对应的数码管)
        self._STB(1)                                   # 关闭片选

    def read(self):                                    # 从TM1638读取按键值
        self._STB(0)                                   # 开启片选
        self._write_byte(_DATACMD | 0x02)              # 42h命令：读取键值
        sleep_us(_TWAIT_US)                            # 读取按键命令与读取按键数据之间至少延时2us
        self._DIO.init(Pin.IN,Pin.PULL_UP)             # DIO引脚切换为输入模式
        for i in range(4): self._read_byte(i) 
        self._DIO.init(Pin.OUT,Pin.PULL_UP)
        self._STB(1)                                   # 关闭片选
        # 查找对应的按键并以列表形式返回按键编号(1-16)，列表内有多个元素则表示为组合键
        return [_KEYS.index(pair)+1 for pair in enumerate(self._key) if pair[1]]
        
    def show(self,data:str,bright=6,left_aligned=False,reverse=True):
        # bright:亮度 left_aligned:左对齐 reverse:若寄存器0对应的数码管在最右侧，需反转以符合阅读习惯
        # 遍历data,检查数码管数量是否够用，不够用则截取data左侧部分作为有效数据
        n=1                                            # 有效字符数即是要用到的数码管数量,首字符总是保留
        last=0                                         # 要截取的结束位置
        for i in range(1,len(data)):
            if n>=self._segs:                          # 已经找全
                last = i;  break
            if data[i]!='.': n+=1                      # 当前字符不是小数点
            elif data[i-1]=='.': n+=1                  # 当前字符是小数点，但前一字符含有小数点
        if last: data = data[0:last]
        rs,re = (0,n) if left_aligned else (self._segs-n,self._segs)  # _buf有效数据下标的起止位置
       
        # self._buf前16字节赋值
        for i in range(rs): self._buf[i]=0x00                        # 右对齐时，左侧无数据时显示空格
        for i in range(re,self._segs): self._buf[i]=0x00              # 左对齐时，右侧无数据时显示空格
        for i in range(len(data)):
            c=ord(data[i])
            if ord('0') <= c <= ord('9'): self._buf[rs]=_SEGS[c-ord('0')]      # 数字
            elif ord('A') <= c <= ord('Z'): self._buf[rs]=_SEGS[c-ord('A')+10] # 大写字母
            elif ord('a') <= c <= ord('z'): self._buf[rs]=_SEGS[c-ord('a')+10] # 小写转为大写字母
            elif c==ord('.'):                                                  # 小数点
                if i and data[i-1]!='.':              # 小数点不是首个字符,且上一个LED不含小数点
                    self._buf[rs-1]|=0x80             # 上一个LED加上小数点
                    continue                          # rs不需要加1，因不额外占用寄存器
                else: self._buf[rs]=0x80              # 当前LED显示小数点
            elif c==ord('-'): self._buf[rs]=0x40      # -(负号)
            elif c==ord('*'): self._buf[rs]=0x63      # *
            else: self._buf[rs]=0x00                  # 空格和其它任何字符都显示为空格
            rs+=1                                     # 下标向后移动一位 
        
        # 完成上述步骤后，才可以反转，因为小数点可能不是独立的一位
        if reverse:
            for i in range(self._segs//2):
                self._buf[i],self._buf[self._segs-1-i]=self._buf[self._segs-1-i],self._buf[i] 
        # 转化为共阳极位图：将self._buf的前16个字节转化到后16个字节
        if self._comm_anode:  # 共阳极数码管的数据处理,每个地址(c0/c2/c4.../ce)都包含8个字符的一段
            for i in range(8):
                self._buf[i+16]=0                     # 前8个数码管
                if self._segs>8: self._buf[i+24]=0    # 第9、10个数码管
                for j in range(8):                    # 保存所有LED的第i段到该缓存的j段
                    self._buf[i+16] |= ((self._buf[j]>>i) & 1)<<j 
                    if self._segs>8:  self._buf[i+24] |= ((self._buf[8+j]>>i) & 1)<<j
            
        self._write_cmd(_DATACMD)                     # 命令40h：地址自增模式写入
        self._write_buf()                             # 地址自增模式写入数据
        self.brightness(bright)                       # 显示控制命令
        
    def brightness(self,val=None):                    # 返回亮度，或者开启显示并设置亮度'
        if val is None: return self._brightness
        self._brightness = val%8 
        self._write_cmd(_DISCTRL | 0x08 | self._brightness)
        
    def power_off(self):                              # 关闭显示
        self._write_cmd(_DISCTRL)                     #0x80 
