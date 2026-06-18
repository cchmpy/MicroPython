class MyList:
    def __init__(self, data):                    # 对象创建后用于初始化的特殊方法
        self._data = data
    def __getitem__(self, index):                # 序列协议要求实现的特殊方法，可用于索引和切片
        if isinstance(index, slice):                                 # 检查是否为slice的实例
            return self._data[index.start : index.stop : index.step] # 切片操作，slice的三个属性
        else:
            return self._data[index]                                 # 索引操作
a = MyList([0, 1, 2, 3, 4, 5])
print(a[1:4])                                    # [1, 2, 3]（自动处理 slice 对象）
