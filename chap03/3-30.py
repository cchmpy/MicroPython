# 示例1：可迭代对象（Iterable）
class MyIterable:
    def __init__(self, data):
        self._data = data    
    def __iter__(self):
        return iter(self._data)  # 返回一个迭代器

my_list = MyIterable([1, 2, 3])
for x in my_list:        # 隐式调用 iter(my_list)
    print(x,end=' ')     # 1 2 3

# 可以重复迭代或遍历
for x in my_list:                 
    print(x,end=' ')     # 1 2 3

# 示例2：迭代器（Iterator）
class MyIterator:
    def __init__(self, data):
        self.data = data
        self.index = 0    
    def __iter__(self):
        return self        # 迭代器自身是可迭代的 
    def __next__(self):
    # 当完成迭代后不能重复迭代
        if self.index >= len(self.data): 
            raise StopIteration
        value = self.data[self.index]
        self.index += 1
        return value

iterator = MyIterator([1, 2, 3])
for x in iterator:
    print(x,end=' ')       # 1 2 3
try:
    print(next(iterator))  # 不能继续迭代
except StopIteration: pass

def my_generator(data):    # 使用生成器定义迭代器
    for item in data:
        yield item         # 自动转换为生成器迭代器

print(type(my_generator))  # <class 'generator'>
gen = my_generator([1, 2, 3])
for x in gen:  print(x,end=' ')       # 1 2 3 
# 无法重复迭代或遍历
for x in gen: print(x,end=' ')       # 不会被执行
