from machine import Pin
from time import ticks_us, ticks_diff, sleep_ms
from micropython import schedule
class IrRxNec:
    def __init__(self,pin_rx, filter_us=100):
        self._pin_rx = Pin(pin_rx,mode=Pin.IN,pull=Pin.PULL_UP)         # 红外接收引脚
        self._filter_us = filter_us            # 待滤除杂波的脉宽
        self._code   = bytearray(4)            # 保存接收的红外数据（地址码和指令码）
        self._reset_receiver()                 # 重置接收器状态
        self._rx_leader = False                # 是否收到引导码
        
        self._callback = None                  # 用户指定的接口函数,接受3参数(地址码,指令码,重复码次数)
        self._addr   = 0                       # 设备地址码(扩展协议为16bit)
        self._prev   = ticks_us()              # 前一个计时,用于计算脉宽
        self._pin_rx.irq(handler=self._handle,trigger=Pin.IRQ_FALLING)   # 定义引脚中断回调
        
    def _reset_receiver(self):                 # 重置接收器状态
        self._shift = 0                        # 接收到的比特位数列
        self._repeat = 0                       # 接收到的重复码的次数
        self._valid = False                    # 红外遥控信号是否有效 
        for i in range(4): self._code[i] = 0   # 地址码和指令码的缓存清零
    
    def set_callback(self,callback=None):      # 驱动程序用户用于设置个性化处理接口
        self._callback = callback
    
    @micropython.viper
    def _rx_one_bit(self,bit_one:int):         # 处理收到的1个比特位
        shift = int(self._shift)               # 强制类型转换后，才能进行算术运算(viper的限制)
        code = ptr8(self._code)                # 强制类似转换
        if self._rx_leader and shift<32:                         # 接收数据bit位数少于32个
            if bit_one: code[shift//8] |= 1<<(shift%8)           # 若是二进制1,则移位,0不用
            shift += 1                                           # 接收的比特位数加1
            self._shift=shift
            if shift==32:                                        # 若接收了32个bit位                 
                self._rx_leader = False                          # 准备下次接收引导码
                if self._callback and (code[2] ^ code[3])==0xFF: # 验证指令码 
                    self._valid = True                    
                    if (code[0] ^ code[1])==0xFF:                # 8bit地址码
                        self._addr = code[0]
                    else:
                        self._addr = code[1]<<8 | code[0]        # 16bit地址码                    
                    schedule(self._callback,(self._addr,self._code[2],self._repeat)) # 调度执行接口函数
    
    @micropython.viper
    def _handle(self,pin):                            # 红外引脚中断回调函数
        cur = ticks_us() 
        p = int(ticks_diff(cur,self._prev))           # 两个下降沿之间的时间,即引导码、重复码或比特位的周期       
        self._prev = cur                              # 更新前一个中断计时
        if p<int(self._filter_us) or p>15000: return  # 脉宽滤波,或遇到引导码或重复码开头的下降沿
        
        if 820<p<1420: self._rx_one_bit(0)            # 比特0的周期是1120±300us
        elif 1840<p<2640: self._rx_one_bit(1)         # 比特1的周期2240±400us
        elif 10250<p<12250:                           # 重复码的周期是11250±1000us
            self._repeat = int(self._repeat)+1        # 收到重复码次数
            if self._valid: schedule(self._callback,(self._addr,self._code[2],self._repeat))
        elif 12500<p<14500:                           # 引导码的周期是13500±1000us,准备接收新信号 
            self._reset_receiver()                    # 重置接收器
            self._rx_leader = True                    # 收到引导码
            
if __name__=='__main__':
    def callback(data):                 # 定义红外数据处理函数
        addr,cmd,repeat = data          # 地址、指令、重复码次数
        print(hex(addr),cmd,repeat)
    irrx = IrRxNec(22)
    irrx.set_callback(callback)
    try:
        while True: sleep_ms(1000)      # 主循环中会自动接收红外遥控信号，并打印相关信息
    except KeyboardInterrupt:  pass