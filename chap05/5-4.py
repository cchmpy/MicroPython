from collections import deque
a, dq1, dq2= [1,2,'a','b'],None, None # 全局变量
def print_dq(dq):                     # 打印双端队列内元素的函数 
    for x in dq: print(x,end=' ')     # 双端队列支持迭代
    print()

try:
    dq1 = deque(a,3,0)                # 创建成功  
    dq2 = deque(a,3,1)                # 创建失败，溢出错误
except IndexError as err: print(err)  # 输出:full
if dq1: print_dq(dq1)                 # 打印dq1的元素，输出：2 a b
if dq2: print_dq(dq2)                 # dq2为None，不打印

# extend()方法测试
dq2 = deque('',3,1)                   # 使用空字符串，定义一个空双端队列
print(len(dq2))                       # 输出：0
try:
    dq2.extend(a)                     # 溢出错误，只添加了部分元素
except IndexError as err: print(err)  # 输出:full
print_dq(dq2)                         # 打印dq2的元素，输出：1 2 a

# 双端队列支持索引取值和赋值（但不支持切片）、迭代、成员检测
dq1[-1] = 10
if 10 in dq1: print(dq1[-1])          # 输出10
print(dq1.extend(a))
