import time, dcmotor                       # 引入程序14-6.py（dcmotor）
from machine import Counter, Timer
ppr,ratio =13, 90                          # 编码器分辨率、直流电机减速比
motor = dcmotor.DCMotor([18,19])           # 直流电机驱动对象
motor.drive(60)                            # 启动电机,可调整占空比(大小或正负)

def handle(_):                             # 定时器中断回调
    global counter
    pps = counter.value(0)                 # 每秒脉冲数，读取计数器并重置为0
    rpm = pps*60//(ppr * ratio)            # 每分钟转速
    print(f'{pps}pps {rpm}rpm \r',end='')  # 单行打印信息
# 使用完整参数定义Counter对象，同时开始计数
counter = Counter(0,src=23,edge=Counter.FALLING,direction=Counter.UP,filter_ns=13000)
timer = Timer(0,mode=Timer.PERIODIC,period=1000,callback=handle)  # 定义并启动定时器对象

try:
    while True: time.sleep(1)
except KeyboardInterrupt: 
    motor.deinit();  counter.deinit()
