import time, dcmotor                       # 引入程序14-6.py（dcmotor）
from machine import Encoder, Timer
ppr,ratio =13, 90                          # 编码器分辨率、直流电机减速比
motor = dcmotor.DCMotor([18,19])           # 直流电机驱动对象
motor.drive(left_duty=60)                  # 启动电机,可调整占空比(大小或正负)
phases = 4                                 # 倍频或相位数
def handle(_):                             # 定时器中断回调
    global encoder
    pps = encoder.value(0)                 # 每秒脉冲数，读取计数器并重置为0
    rpm = pps*60//(phases * ppr * ratio)   # 每分钟转速
    print(f'{pps}pps {rpm}rpm \r',end='')  # 单行打印信息
# 使用完整参数定义Encoder对象，同时开始计数
encoder = Encoder(0, phase_a=23, phase_b=22, phases=phases, filter_ns=13000)
timer = Timer(0,mode=Timer.PERIODIC,period=1000,callback=handle)  # 定义并启动定时器对象

try:
    while True: time.sleep(1)
except KeyboardInterrupt: 
    motor.deinit(); encoder.deinit()