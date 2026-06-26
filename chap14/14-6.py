from machine import PWM
class DCMotor:
    def __init__(self,in_pins,freq=5000):
        self._freq = freq                                       # PWM信号频率
        self._ins = [PWM(p,freq,duty=0) for p in in_pins]       # 逻辑输入控制引脚，依次in1、in2、in3、in4        
    
    def drive(self,left_duty=0,right_duty=0):                   # left_duty、right_duty是占空比
        left = abs(left_duty*1023//100)                         # 将占空比换算为duty（0-1023）
        rigtht = abs(right_duty*1023//100)
        try:
            if left_duty>=0:
                self._ins[0].duty(left)
                self._ins[1].duty(0)
            else:
                self._ins[0].duty(0)
                self._ins[1].duty(left)
            if right_duty>=0:
                self._ins[2].duty(right)
                self._ins[3].duty(0)
            else:
                self._ins[2].duty(0)
                self._ins[3].duty(right)
        except IndexError: pass                                  # 如果只用in1、in2驱动一个电机，处理索引异常
    
    def freq(self,freq=None):                                    # 获取和设置PWM信号的频率
        if freq is None: return self._freq
        self._freq = freq
        for p in self._ins: p.freq(freq)
           
    def deinit(self):
        for p in self._ins: p.deinit()
