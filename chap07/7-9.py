from machine import TouchPad,Pin
import time,sys
s3 = 'ESP32S3' in sys.implementation._machine # 是否为ESP32-S3
t = TouchPad(12)                              # 触摸对象
led = Pin(23,mode=Pin.OUT,value=0)            # LED灯
baseline = 0                                  # 基线值
sensitivity = 0.3                             # 灵敏度因子，越小越敏感，可根据实验调整
noise_threshold = 1000 if s3 else 10          # 噪声阈值，小于此值的变化忽略不计

print("校准中,请勿触摸...")                     # 开始进行校准基线
time.sleep(1)
cnt = 100
for i in range(cnt):
    baseline += t.read()
    time.sleep(0.01)
baseline //= cnt                              # 计算滚动平均值作为基线
print("校准完成,基线值:", baseline)

while True:
    value = t.read()
    change = abs(baseline - value)            # 计算测量值与基线的差值
    per  = change/baseline                    # 变化百分比
    if change>noise_threshold and per>sensitivity: # 变化值超过噪声阈值和灵敏度要求
        print(f"检测到触摸，测量值:{value} 变化:{per:0.1%}")
        led.toggle()                          # 切换LED开关状态或进行其它操作
        time.sleep_ms(500)                    # 有触摸时，简单延时去抖
    else:
        # 无触摸时，缓慢更新基线以适应环境变化（温漂）
        baseline = baseline*0.99+value*0.01   # 一阶低通滤波
    time.sleep_ms(50)                         # 无触摸时短延时
