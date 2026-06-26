from machine import Pin
from time import sleep_us,sleep_ms
from micropython import const
MODE_S_4 = const(0)                             # 单四拍模式
MODE_D_4 = const(1)                             # 双四拍模式
MODE_8   = const(2)                             # 八拍模式
_CW_S_4  = b'\x08\x04\x02\x01'                  # 单四拍通电时序编码，顺时针
_CW_D_4  = b'\x0c\x06\x03\x09'                  # 双四拍通电时序编码，顺时针
_CW_8    = b'\x08\x0c\x04\x06\x02\x03\x01\x09'  # 八拍通电时序编码，顺时针
_CW = (_CW_S_4,_CW_D_4,_CW_8, bytes(reversed(_CW_S_4)),  # CW(顺时针)、CCW(逆时针)通电时序编码
       bytes(reversed(_CW_D_4)), bytes(reversed(_CW_8)),) 

class ULN2003:
    def __init__(self,in1, in2, in3, in4,mode=MODE_8,freq_full_step=550,spr_full_step=2037.8864):
        # 整步模式下，64:1减速电机单圈步数=4*8*63.68395 = 2037.8864 
        self._pinA = Pin(in1,Pin.OUT)
        self._pinB = Pin(in2,Pin.OUT)
        self._pinC = Pin(in3,Pin.OUT)
        self._pinD = Pin(in4,Pin.OUT)
        self._freq_full_step = freq_full_step   # 整步模式下启动频率
        self._spr_full_step = spr_full_step     # 整步模式下旋转一周的步数 spr(steps per revolution)
        self.mode(mode)                         # 增加或更新成员变量：self._mode、self._delay_us
        self.stop()
        
    def _set_pin(self, step_val):               # 设置引脚（电机的四相）电平        
        self._pinA(step_val & 0x08)
        self._pinB(step_val & 0x04)
        self._pinC(step_val & 0x02)
        self._pinD(step_val & 0x01)        
        sleep_us(self._delay_us) 
    
    def _delay(self):                           # 计算当前模式和频率下，两步之间的间隔时间 
        t = 2 if self._mode==MODE_8 else 1
        self._delay_us = int(1000_000/(self._freq_full_step * t))
        
    def mode(self, mode=None):                  # 设置或获取工作模式
        if mode is None: return self._mode
        if mode not in (MODE_8,MODE_D_4,MODE_S_4):
            raise ValueError('Mode must be in (0,1,2)')
        else:
            self._mode = mode 
            self._delay()
        
    def freq(self,freq_full_step=None):        # 获取和设置整步模式下的启动频率
        if freq_full_step is None: return self._freq_full_step 
        if freq_full_step:
            self._freq_full_step = min(freq_full_step,550)
            self._delay() 
        
    def stop(self):                            # 电机转动完成后可将所有相电压置零，节能防发热 
        self._set_pin(0)
        
    def steps(self,steps,cw=True,lock=False):  # 按设定方向转动steps步，cw:是否顺时针，lock:是否锁定
        j = self._mode+(0 if cw else 3)        # 根据方向确定相序序列索引偏移量 
        len_pha = len(_CW[j]) 
        for i in range(steps):
            self._set_pin(_CW[j][i%len_pha]) 
        if not lock: self.stop() 
                
    def angle(self,degree,cw=True,lock=False): # 按设定方向转动角度degree
        t = 2 if self._mode==MODE_8 else 1
        steps = int(degree * self._spr_full_step * t / 360)
        self.steps(steps,cw,lock)

if __name__ == '__main__':
    from machine import Timer
    uln = ULN2003(19,21,22,23) 
    uln.angle(90,False)                        # 默认8拍半步模式，逆时针转90°    
    uln.mode(MODE_D_4); uln.angle(90,True)     # 4拍针步模式，顺时针转90°
    # 模拟时钟的秒针转动
    uln.mode(MODE_8)
    timer1 = Timer(1)
    timer1.init(period=1000, mode=Timer.PERIODIC, callback=lambda _:uln.angle(6))
    try:
        while True: sleep_ms(1000)
    except KeyboardInterrupt: timer1.deinit()
