# 示例1：实现矩阵的乘法（@运算符）
class Matrix:
    def __init__(self, data):
        self.data = data          # 假设是二维列表
    def __matmul__(self, other):  # 实现矩阵乘法
        result = [
            [sum(a * b for a, b in zip(row, col)) 
            for col in zip(*other.data)]
            for row in self.data
        ]
        return Matrix(result)     # 返回对象
    def __repr__(self):
        return f"Matrix({self.data})"
A = Matrix([[1, 2], [3, 4]])
B = Matrix([[5, 6], [7, 8]])
print(A @ B)  # 输出: Matrix([[19, 22], [43, 50]])

# 示例2：实现+=运算符
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
