import time
i = 0
try:  
    while True:                       # 无限循环        
        print(f'{i}\r',end='')        # 在同一行打印程序运行的秒数      
        time.sleep(1)                 # 暂停1秒
        i += 1
except KeyboardInterrupt:             # 捕获键盘中断Ctrl+c
    print('\nProgram stopped.')       # 打印提示信息
    