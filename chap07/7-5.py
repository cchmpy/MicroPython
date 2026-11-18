import micropython,time
from machine import Timer
micropython.alloc_emergency_exception_buf(100) # 分配紧急异常缓冲区
alloc = False; irq = False             # 测试标志：是否分配内存、是否触发中断                       

def handle(_):                         # 可能进行内存分配的中断回调函数
    global alloc, irq
    irq = True
    try:                               # try块包裹待测试代码
        a = 10;  a +=3.14              # a +=3.14将分配堆内存
    except MemoryError: alloc = True   # 设置分配内存标志

def test():
    timer = Timer(1,mode=Timer.ONE_SHOT,period=200,callback=handle)
    micropython.heap_lock()            # 锁堆
    time.sleep(0.5)                    # 等待中断触发
    timer.deinit()                     # 移除中断处理
    micropython.heap_unlock()          # 解锁
    if alloc and irq: print('ISR分配了堆内存') 
    elif irq: print('ISR未分配堆内存')
    else: print('未触发中断')   
test()                                 # 运行测试
