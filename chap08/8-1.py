from machine import lightsleep
import esp32, time
if hasattr(esp32,'raw_temperature'):     # ESP32
    temperature = lambda: f'{(esp32.raw_temperature()-32)*5/9:.2f}' # 华氏度转摄氏度
elif hasattr(esp32, 'mcu_temperature'):  # ESP32C3/C6、ESP32S2/S3
    temperature = esp32.mcu_temperature
else:
    temperature = lambda:'Unable to obtain'
a = 0
for i in range(100000): a += 1           # 热身，芯片内部温度略升高
print(temperature(),'℃',sep='')         # 打印睡眠前，CPU内部温度
time.sleep_ms(50)                        # 防止未完成打印，就进入睡眠
lightsleep(10_000)                       # 进入睡眠，10秒后唤醒
print(temperature(),'℃',sep='')         # 打印睡眠后，CPU内部温度
