import time, dcmotor                             # 导入程序14-6.py（dcmotor.py）
from pid import IncrementalPID as PID            # 导入程序14-7.py（pid.py）
from machine import Timer, Encoder
motor = dcmotor.DCMotor([18,19])                 # 定义电机驱动对象
motor.drive(70)                                  # 以70%功率启动
encoder = Encoder(0, phase_a=23, phase_b=22, phases=4, filter_ns=13000) # 解码器4x脉冲计数
pid = PID(kp=0.02, ki=0.0126, kd=0, output_min=-70, output_max=30)      # 增量式PID控制器    

def timer_cb(t):                                 # 定时器中断回    
    cur_v = encoder.value(0)                     # 周期内脉冲数，读取计数器并重置为0
    motor.drive(70+int(pid.compute(3000,cur_v))) # 目标3000，当前值cur_v
    print(cur_v)    
timer = Timer(1,mode=Timer.PERIODIC,period=500,callback=timer_cb)       # 定义并启动定时器
try:
    while True: time.sleep(1)
except KeyboardInterrupt:
    timer.deinit(); encoder.deinit(); motor.deinit()