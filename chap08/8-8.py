import micropython,time
from machine import Timer
micropython.alloc_emergency_exception_buf(100) # 分配紧急异常缓冲区
alloc = False                          # 测试标志：是否分配内存
irq   = False                          # 测试标志：是否触发中断

def handle(_):                         # 可能进行内存分配的中断回调函数
    global alloc, irq
    irq = True
    try:                               # try块包含了待测试代码        
        buf = bytearray(10)            # 将分配内存
        # new_list = [1, 2, 3]         # 将分配内存
        # new_dict = {"key": "value"}  # 将分配内存        
        # formatted = f'Value: {irq}'  # 将分配内存
        # result = 1.0 + 2.0           # 不分配内存
        # buf = b'abcd'                # 不分配内存
    except MemoryError: alloc = True
    
def test():
    global handle, alloc, irq
    timer = Timer(1,mode=Timer.ONE_SHOT,period=200,callback=handle) # 定时器对象   
    micropython.heap_lock()            # 锁堆
    time.sleep(0.5)                    # 等待中断触发
    timer.deinit()                     # 移除中断处理
    micropython.heap_unlock()          # 解锁
    # 打印测试结果
    if alloc and irq: print('ISR中有堆内存分配')    
    elif irq: print('ISR中未分配内存')
    else: print('未触发中断')
    
test()                                 # 运行测试