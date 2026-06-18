class MutableList:
    def __init__(self, data):
        self.data = data    
    def __iadd__(self, other):
        self.data.extend(other.data)
        return self       # 必须返回self

a = MutableList([1, 2])
b = MutableList([3, 4])
a += b                    # a.data变为[1, 2, 3, 4]
print(a.data)
