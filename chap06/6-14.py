import machine, time
wdt = machine.WDT(timeout=5000)          # 如果在5秒内没有喂狗，ESP32将自动重启 
try:
    counter = 0                          # 主循环次数
    while True: 
        print("正在执行任务...", counter) # 模拟主循环中执行的一些正常任务
        counter += 1;  time.sleep(1)     # 每秒执行一次循环
        if counter == 6:                 # 模拟一个随机发生的错误（第6次循环时“死机”）
            print("模拟程序出错，进入死循环...")
            while True: time.sleep(0.1)  # 这是一个死循环
        wdt.feed()                       # 喂狗，告诉看门狗系统一切正常
except Exception as err: print(err)      # 即使捕获异常，只要没喂狗，也会触发硬复位 

