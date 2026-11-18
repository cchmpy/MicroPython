from machine import ADC,mem32,Pin,deepsleep,lightsleep
from micropython import const
import time,esp32

_RTC_CNTL_STORE0_REG = const(0x3FF4804C)   # 保留寄存器地址,使用低地址2个比特位
_MOISTURE_MAX = const(2000)                # 土壤水分饱和时ADC传感器的值(mv)
_MOISTURE_MIN = const(1200)                # 土壤干燥需灌溉时ADC传感器的值(mv)
_SENSOR = const(36)                        # 土壤湿度传感器引脚
_CONTROL = const(32)                       # 灌溉控制引脚
_TIME_SLEEP  = const(5000)                 # 非灌溉时的睡眠时长(毫秒)
_TIME_WATER  = const(5000)                 # 单次灌溉时长（一次完整灌溉分多次进行）
_TIME_PAUSE  = const(5000)                 # 单次灌溉后的暂停时长（等待水分渗透）
water = Pin(_CONTROL,mode=Pin.OUT,value=0) # 控制引脚
sensor = ADC(_SENSOR,atten=ADC.ATTN_11DB)  # ADC传感器
def hint(info):                            # 信息提示函数 
    print(info)
    time.sleep(0.2) 
 
while True:                                # Light-sleep后的程序入口
    watering = mem32[_RTC_CNTL_STORE0_REG] # 读取灌溉状态标志    
    sum_,n = 0, 10                         # 测量n次求平均
    for i in range(n): 
        sum_ += sensor.read_uv()
        time.sleep(0.2)        
    result = sum_//(n*1000)                # 计算平均值(mv)
    print(watering,result)                 # 打印状态和测量结果

    if watering & 1:                       # 是否处于灌溉状态
        if result<_MOISTURE_MAX:           # 湿度不达标
            if watering & 2:               # 上次是灌溉,此次暂停
                water(0)
                mem32[_RTC_CNTL_STORE0_REG] = 1    # 记录当前状态：灌溉状态但没有进行
                hint('暂停灌溉')
                deepsleep(_TIME_PAUSE)     # 暂停期间深度睡眠
            else:
                water(1)                   # 上次暂停,此次灌溉
                mem32[_RTC_CNTL_STORE0_REG] = 3 
                hint('继续灌溉')
                lightsleep(_TIME_WATER)    # Light-sleep是为了睡眠期间保持引脚状态
        else:                              # 处于灌溉状态但已达标
            water(0)
            mem32[_RTC_CNTL_STORE0_REG] = 0
            hint('停止灌溉')
            deepsleep(_TIME_SLEEP)
    else:
        if result<_MOISTURE_MIN:            # 需要灌溉
            water(1)
            mem32[_RTC_CNTL_STORE0_REG] = 3 # 设置灌溉标志
            hint('开始灌溉')
            lightsleep(_TIME_WATER) 
        else:           
            hint('无需灌溉')
            deepsleep(_TIME_SLEEP)          # 无需灌溉
