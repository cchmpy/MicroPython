import gc
def alloc(size): 
    bytearray(size)                   # 分配内存，定义一个引用计数为0的对象
    print(gc.mem_alloc())             # 打印已分配堆内存的字节数

gc.collect()                          # 进行一次垃圾回收，此时是内存分配的计数起点
print('threshold:',gc.threshold())    # 打印当前阈值，输出: threshold: -1
for i in range(20): alloc(1024*5)     # 每次分配5KiB,默认大约累计50Kib时触发自动回收

print('----------threshold---------') # 以下是设置阈值后的情况(上次垃圾回收是计数起点)
gc.threshold(20000)
for i in range(20): alloc(1024*5)     # 每次分配5KiB,累计大约20000字节时触发自动回收
