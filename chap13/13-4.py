from machine import PWM
class DCMotor:
    def __init__(self,in_pins,freq=5000):
        self._freq = freq                      # PWM信号频率
        # in_pins是包含逻辑输入控制引脚的列表或园区，如[in1、in2、in3、in4]
        self._ins = [PWM(p,freq,duty=0) for p in in_pins]
    def drive(self,left_duty=0,right_duty=0):  # left_duty、right_duty是占空比
        left = abs(left_duty*1023//100)        # 将占空比换算为duty（0-1023）
        right = abs(right_duty*1023//100)
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
        except IndexError: pass      # 若只用in1、in2驱动一个电机，处理索引异常
    def freq(self,freq=None):                  # 获取和设置PWM信号的频率
        if freq is None: return self._freq
        self._freq = freq
        for p in self._ins: p.freq(freq)
    def deinit(self):
        for p in self._ins: p.deinit()
if __name__ == '__main__':
    from time import sleep
    m = DCMotor([18,19,22,23])
    m.drive(0,0)                   # 停止
    m.drive(100,100);  sleep(2)    # 全速前进
    m.drive(100,-100); sleep(1)    # 全速右转
    m.drive(40,80);    sleep(1)    # 小角度左转
    m.deinit()