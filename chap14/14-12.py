from machine import Pin, Timer
from time import sleep_us,sleep_ms
from micropython import const
# 步进电机励磁/细分模式: 通过拨码开关状态定义
MODE = {(0,0,0):1, (1,0,0):2, (0,1,0):4, (1,1,0):8,    # (MS1,MS2,MS3):steps
        (0,0,1):16, (1,0,1):32, (0,1,1):32,(1,1,1):32}
# 步进电机励磁/细分模式：通过整数常量定义
MODE_FULL_STEP   = const(1)    # 整步，1细分
MODE_HALF_STEP   = const(2)    # 半步，1/2细分
MODE_QUARTER_STEP= const(4)    # 1/4细分
MODE_1_8_STEP    = const(8)    # 1/8细分
MODE_1_16_STEP   = const(16)   # 1/16细分
MODE_1_32_STEP   = const(32)   # 1/32细分

class DRV8825:
    def __init__(self,pin_dir, pin_step, pin_en,mode=MODE_QUARTER_STEP,
                 freq_full_step=500,spr_full_step=200):
        self._pin_dir  = Pin(pin_dir,Pin.OUT,value=0)   # 转动方向控制引脚
        self._pin_step = Pin(pin_step,Pin.OUT,value=0)  # 步数控制引脚,上升沿触发
        self._pin_en   = Pin(pin_en,Pin.OUT,value=1)    # 使能控制引脚,低电平有效
        self._freq_full_step = freq_full_step           # 整步模式下启动频率
        self._spr_full_step = spr_full_step     # 整步模式下旋转一周的步数 spr(steps per revolution)
        self.mode(mode)                         # 增加或更新成员变量：self._mode、self._delay_us
        self.enable(False) 
    
    def _delay(self):                           # 计算当前模式和频率下，高低电平保持时间(半周期) 
        self._delay_us = 500_000//(self._freq_full_step * self._mode)
        
    def mode(self, mode=None):                  # 获取或设置细分模式
        if mode is None:
            return self._mode
        if isinstance(mode, int):               # mode是整数，如1
            if mode in MODE.values(): self._mode = mode
            else: raise ValueError('Invalid Integer')
        elif isinstance(mode, tuple):           # mode是元组，如(1,0,0)
            m = MODE.get(mode,None)
            if m: self._mode = m
            else: raise ValueError('Mode must be a tuple of 3 numbers(0 or 1)')
        else:
            raise ValueError('Mode must be a int or a tuple of 3 numbers(0 or 1)') 
        self._delay()
        
    def freq(self,freq_full_step=None):          # 获取和设置：整步模式下的启动频率
        if freq_full_step is None: return self._freq_full_step 
        if freq_full_step:
            self._freq_full_step = freq_full_step
            self._delay() 
        
    def enable(self,en=True):                    # 是否允许设备工作
        self._pin_en(not en)                     # 低电平有效

    def steps(self,steps=1,cw=True, lock=True):  # 按设定步数和方向转动
        self._pin_dir(cw)                        # 设置方向控制引脚
        if self._pin_en():  self.enable(True)    # 驱动器使能（低电平有效）
        for _ in range(steps): 
            self._pin_step(1)                    # 上升沿触发步进
            sleep_us(self._delay_us) 
            self._pin_step(0)
            sleep_us(self._delay_us)
        if not lock: self.enable(lock)           # 要限定位置，必须锁定或使能
        
    def angle(self,degree,cw=True, lock=True):   # 按设定角度和方向转动
        steps = int(degree * self._spr_full_step * self._mode / 360)
        self.steps(steps,cw,lock)

if __name__=='__main__':                         # 驱动42步进电机17HS4023,模拟时钟的秒针转动
    from machine import Timer
    step = DRV8825(16,17,18,freq_full_step=1500,spr_full_step=200)
    step.mode(MODE_1_16_STEP)                    # 16细分
    timer1 = Timer(1)
    timer1.init(period=1000, mode=Timer.PERIODIC, callback=lambda _:step.angle(6,False,True))
    try:
        while True: sleep_ms(1000)
    except KeyboardInterrupt:
        timer1.deinit()
        step.enable(False)                       # 禁止驱动器工作，线圈无电流，减少能耗和发热
