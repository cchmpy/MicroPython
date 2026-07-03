import esp32,time,machine
# 定义复位和唤醒原因的字典
reset={1:'PWRON_RESET',2:'HARD_RESET',3:'WDT_RESET',4:'DEEPSLEEP_RESET',5:'SOFT_RESET'}
wake={2:'EXT0_WAKE',3:'EXT1_WAKE',4:'TIMER_WAKE',5:'TOUCHPAD_WAKE',6:'ULP_WAKE'}

# 设置唤醒源,ext0不能与触摸唤醒和ULP唤醒同时使用
machine.TouchPad(12).config(300)              # ESP32的触摸阈值设为300
esp32.wake_on_touch(True)                     # 设置触摸传感器唤醒源
esp32.wake_on_ulp(True)                       # 设置协处理器唤醒源
esp32.wake_on_ext1((4,),esp32.WAKEUP_ANY_HIGH)# 设置外部唤醒源ext1
print('Zzzz...')
time.sleep_ms(50)                             # 等待打印完成
# machine.deepsleep(5000)
machine.lightsleep(5000)                      # 睡眠,同时设置定时器唤醒

rs = machine.reset_cause()                    # 重置原因
wr = machine.wake_reason()                    # 唤醒原因
print(f'reset_cause:{reset[rs]}  wake_reason:{wake[wr]}')
esp32.wake_on_touch(False)                    # 禁用触摸传感器唤醒源
esp32.wake_on_ulp(False)                      # 禁用协处理器唤醒源
esp32.wake_on_ext1(None)                      # 禁用外部唤醒源ext1
