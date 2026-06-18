class MyIterable:
    def __init__(self, data):
        self._data = data    
    def __iter__(self):
        return iter(self._data)  # 返回一个迭代器

my_list = MyIterable([1, 2, 3])
for x in my_list:                # 隐式调用 iter(my_list)
    print(x,end=' ')             # 1 2 3

# 可以重复迭代或遍历
for x in my_list:                 
    print(x,end=' ')     # 1 2 3
