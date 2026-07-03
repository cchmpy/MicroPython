from machine import lightsleep
import esp32,time
if hasattr(esp32,'raw_temperature'):     # ESP32
    temperature = lambda: f'{(esp32.raw_temperature()-32)*5/9:.2f}'  # 华氏度转摄氏度
elif hasattr(esp32, 'mcu_temperature'):  # ESP32C3/C6、ESP32S2/S3
    temperature = esp32.mcu_temperature
else:
    temperature = lambda:'Unable to obtain'
a = 0
for i in range(100000): a += 1           # 热身
print(temperature())                     # 打印cpu内部温度
time.sleep_ms(50)                        # 防止打印未完就进入睡眠
lightsleep(10_000)                       # 进入睡眠，10秒后唤醒
print(temperature())