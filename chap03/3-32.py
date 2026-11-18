class MySequence:
    def __init__(self, data):         # 用于类初始化的特殊方法
        self._data = list(data)       # 内部存储数据
    def __len__(self):                # 返回序列长度
        return len(self._data)
    def __getitem__(self, index):     # 支持索引和切片
        if isinstance(index, slice):  # 处理切片
            return MySequence(self._data[index])
        return self._data[index]      # 处理单索引
    def __setitem__(self, index, value): # 支持索引和切片赋值
        self._data[index] = value            
    def __delitem__(self, index):     # 支持通过索引和切片删除数据项
        del self._data[index]        
    def __contains__(self, item):     # 支持in操作符
        return item in self._data
    def __reversed__(self):           # 支持reversed()
        return MySequence(reversed(self._data))
    def __str__(self):                # 打印字符串
        return str(self._data)

seq = MySequence([0, 1, 2, 3, 4])
print(len(seq))                       # 输出:5，支持 len()
print(seq[1])                         # 输出:1，支持索引访问
print(seq[1:4])                       # 输出: [1, 2, 3]，支持切片，返回新的MySequence
print(2 in seq)                       # 输出: True， 支持in操作符
print(reversed(seq))                  # 输出: [4, 3, 2, 1, 0]，支持 reversed()
for item in seq:                      # 支持迭代（因为实现了__getitem__，旧版方法）
    print(item,end=' ')               # 输出: 0 1 2 3 4
print('')                             # 换行
seq[0]=10                             # 索引赋值，seq变成[10, 1, 2, 3, 4]
seq[0:2] = (10,11,12)                 # 切片赋值，seq[10, 11, 12, 2, 3, 4]
