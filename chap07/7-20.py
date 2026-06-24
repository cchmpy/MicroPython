import machine
import time
wdt = machine.WDT(timeout=5000)          # 如果在5秒内没有喂狗，ESP32将自动重启
try:
    counter = 0                          # 主循环次数
    while True:        
        print("正在执行任务...", counter)  # 模拟主循环中执行的一些正常任务
        counter += 1
        time.sleep(1)                    # 每秒执行一次循环        
        if counter == 6:                 # 模拟一个随机发生的错误（第6次循环时“死机”）
            print("模拟程序出错，进入死循环...")
            while True:                  # 这是一个致命的死循环！                
                time.sleep(0.1)          # 5秒后，看门狗超时，系统将自动重启
        wdt.feed()                       # 喂狗，告诉看门狗系统一切正常
except Exception as err:                 # 即使程序因为异常崩溃，只要没喂狗，看门狗最终也会触发复位    
    print(err)
    