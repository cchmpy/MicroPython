from machine import Timer,I2C,Signal,Pin
import time,bmp280,buzzer                         # 引入程序7-14.py、7-10.py
bz  = buzzer.Buzzer(19)                           # 蜂鸣器
bmp = bmp280.BMP280_I2C(I2C(0,scl=23, sda=22))    # 气压传感器
led = Signal(18,mode=Pin.OUT,value=0,invert=True) # 低电平点亮的LED
flag = True                                       # 交替声光报警使能标志 
timer2 = None                                     # 报警用定时器对象,也用来判断是否处于报警状态

def timer2_cb(_):                                 # 报警用定时器中断回调
    global led,bz,flag    
    if flag: bz.tone(1000)                        # 声音报警,发声频率1000Hz                                            
    else:    bz.no_tone()                         # 暂停发声        
    led(flag)                                     # 灯光报警,交替闪灯
    flag = not flag                               # 交替使能

def timer1_cb(_):                                 # 监测用定时器中断回调
    global bmp,bz,led,timer2
    t,p,_ = bmp.get_measurements()                # 在此读取传感器的测量结果
    print(f'{t} {p}  \r',end='')                  # 在LED上显示（这里用打印模拟）
    if t>=28:                                     # 假设温度突破28启动报警（便于测试程序）
        if timer2 is None:                        # 若未处于报警状态,则开启报警
            timer2=Timer(2,mode=Timer.PERIODIC,freq=4,callback=timer2_cb)  # 启动报警用定时器
    else:
        if timer2 is not None:                    # 若处于报警状态,关闭执行器和报警用定时器
            led(0)
            bz.no_tone()
            timer2.deinit()            
            timer2=None     
timer1 = Timer(1,mode=Timer.PERIODIC,freq=0.5,callback=timer1_cb)  # 监测用定时器,2秒的测试间隔    
try:
    while True:time.sleep(1)
except KeyboardInterrupt:
    bz.deinit()    
    timer1.deinit()
    if timer2 is not None:                        # 键盘中断退出时处于报警状态
        led(0)
        Timer2.deinit()

