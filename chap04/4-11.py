# 可调用类实现计数器4-11.py
class Counter:
    def __init__(self):  
        self.count = 0   # 存储状态,相当于闭包捕获的变量
    def __call__(self):  # 定义调用时的行为,相当闭包函数
        self.count += 1
        return self.count
    def reset(self):     # 重置计数
        self.count = 0
c = Counter()            # 类似于闭包c = counter()
print(c())               # 1
print(c())               # 2
c.reset()                # 重置计数
