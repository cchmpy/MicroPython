import time
from machine import ADC
adc = ADC(34, atten=ADC.ATTN_11DB)           # 定义ADC对象
while True:
    t0 = time.ticks_us()                     # 测量开始时间
    v = adc.read_uv()                        # 读取结果
    T = time.ticks_diff(time.ticks_us(),t0)  # 测量所需时间
    print(f'{v//1000}mV {T}us \r',end='')    # 单行打印结果,如:1869mV 85us 
    time.sleep_ms(500)