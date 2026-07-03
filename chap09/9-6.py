import machine,esp32,time
Pin = machine.Pin
esp32.wake_on_ext0(36,esp32.WAKEUP_ANY_HIGH)  # 设置唤醒源,36引脚连接HC-SR501

reset = machine.reset_cause()                 # esp32重置原因
if  reset == machine.PWRON_RESET:             # 系统上电
    time.sleep(60)                            # 等待模块完成初始化
elif reset == machine.DEEPSLEEP_RESET:        # 从Deep-sleep唤醒
    Pin(23,mode=Pin.OUT,value=1)              # 警报触发引脚
    time.sleep(3)                             # 警报持续3秒（实际应更长时间如30秒）
machine.deepsleep()
