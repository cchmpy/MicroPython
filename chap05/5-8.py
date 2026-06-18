import heapq
from random import randint
x = [randint(0,100) for i in range(5)]  # 待建最小堆，含5个随机数的列表
heapq.heapify(x)                        # 建最小堆
print(x)                                # 打印堆结构,输出: [0, 1, 65, 40, 35]

for i in range(5):
    heapq.heappush(x,randint(0,100))    # 向堆中添加5个元素
print(x)                                # 打印堆结构，输出: [0, 1, 65, 38, 35, 80, 87, 40, 39, 92]

try:
    while True:
        print(heapq.heappop(x),end=' ') # 循环弹出所有元素，输出:0 1 35 38 39 40 65 80 87 92 
except IndexError: pass
