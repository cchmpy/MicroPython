import time
def schedule_task(interval_ms):
    last_run = time.ticks_ms()                              # 初始化上次任务执行的时间点
    def task(current_time):                                 # 闭包函数,记住last_run和interval_ms
        nonlocal last_run 
        diff = time.ticks_diff(current_time,last_run)       # 计算距离上次任务执行的时间间隔
        if diff >= interval_ms:
            last_run = current_time
            # 此处执行具体任务,用sleep_ms()和print()函数模拟
            print("Task executed at", current_time)
            time.sleep_ms(15)                                # 模拟任务执行的时间 
            diff = time.ticks_diff(time.ticks_ms(),last_run) # 包含任务执行的时间 
        return interval_ms-diff                              # 返回距离下次执行任务的时间
    return task
# 每1000ms执行一次任务
task = schedule_task(1000)
while True:
    time.sleep_ms(task(time.ticks_ms()))                     # 在任务间隔睡眠，也可增加低功耗措施
