from machine import Timer
from esp32 import PCNT
from micropython import const
PCNT_RANGE = const(30000)                           # 脉冲计数最大值

class PcntEncoder:
    def __init__(self,unit_id, timer_id, pin_a, pin_b=None,
                 ppr=13, ratio=90, filter=1023,multiplier=1): 
        self._a = pin_a; self._b = pin_b            # A、B相引脚
        self._ppr = ppr                             # 编码器分辨率（线数）
        self._ratio = ratio                         # 电机减速比
        self._overflows = 0                         # 达到最大或最小计数值后的溢出次数 
        self._callback = None                       # 用户接口函数
        
        self._pcnt = PCNT(0, min=-PCNT_RANGE, max=PCNT_RANGE, filter=filter)
        self._pcnt.irq(self._pcnt_handle,PCNT.IRQ_MAX | PCNT.IRQ_MIN)
        self.multiplier(multiplier)                 # 设置倍频 
        self._timer = Timer(timer_id)               # 定时器对象
    
    def start(self):                                # 开始或重新开始计数
        self._timer.init(mode=Timer.PERIODIC,period=1000,callback=self._timer_handle)
        self._pcnt.start()
    
    def stop(self):                                 # 停止计数并重置计数寄存器
        self._timer.init(callback=None)
        self._pcnt.stop()
        self._pcnt.value(0)
    
    def deinit(self):                               # 解除定时器和PCNT对象的初始化
        self._timer.deinit()
        self._pcnt.deinit()
    
    def set_callback(self,callback):                # 设置用户回调函数,接受两参数:每秒脉冲数、每分钟转数
        self._callback = callback
        
    def multiplier(self, m=None):                   # 获取或设置倍频,可设置1、2、4
        if m is None: return self._multi
        if m == 1:                                  # 1倍频对应的通道初始化
            self._pcnt.init(channel=0,pin=self._a,rising=PCNT.INCREMENT)
        elif m == 2:                                # 2倍频对应的通道初始化
            self._pcnt.init(channel=0,pin=self._a,rising=PCNT.INCREMENT,falling=PCNT.INCREMENT)
        elif m == 4:                                # 4倍频对应的通道初始化
            if self._b:
                self._pcnt.init(channel=0, pin=self._a, falling=PCNT.INCREMENT,
                                rising=PCNT.DECREMENT, mode_pin=self._b, mode_low=PCNT.REVERSE)
                self._pcnt.init(channel=1, pin=self._b, falling=PCNT.DECREMENT,
                                rising=PCNT.INCREMENT, mode_pin=self._a, mode_low=PCNT.REVERSE)
            else: raise ValueError('The B-phase pin must be provided.')
        else: raise ValueError('multiplier should be 1, 2 or 4.')
        self._multi = m
            
    def _pcnt_handle(self,pcnt):                    # PCNT中断回调函数
        mask = pcnt.irq().flags()                   # 获取触发事件
        if mask & pcnt.IRQ_MIN:   self._overflows -= 1
        elif mask & pcnt.IRQ_MAX: self._overflows += 1
        
    def _timer_handle(self,timer):                  # 定时器中断回调
        value = self._pcnt.value(0)                 # 读取并清零,value()方法可避免竟态条件
        ofs = self._overflows 
        self._overflows = 0
        pps = value+ofs*PCNT_RANGE                  # 每秒脉冲数
        rpm = pps*60//(self._multi*self._ppr * self._ratio)  # 输出轴转速RPM=(每秒脉冲数*60/(multi*ppr*ratio))
        if self._callback: self._callback(pps,rpm)  # 调用用户接口函数
            
if __name__== '__main__':
    import time,dcmotor                             # 引入程序14-6.py（dcmotor）
    motor = dcmotor.DCMotor([18,19])                # 直流电机驱动对象
    motor.drive(left_duty=60)                       # 启动电机,可调整占空比(大小或正负:-100～100)
    
    def callback(pps,rpm):                          # 步骤1：定义用户接口函数
        print(f'{pps} {rpm}rpm \r',end='')          # 单行打印每秒脉冲数和每分钟转速，正负表示方向
    mrpm = PcntEncoder(0,timer_id=1,pin_a=22,pin_b=23) # 步骤2：定义PcntEncoder对象
    mrpm.multiplier(1)                              # 步骤3：设置倍频，可与步骤2合并
    mrpm.set_callback(callback)                     # 步骤4：设置用户接口函数
    mrpm.start()                                    # 步骤5：开始计数
    try:
        while True:  time.sleep(1)
    except KeyboardInterrupt: 
        motor.deinit();  mrpm.deinit()