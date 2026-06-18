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
