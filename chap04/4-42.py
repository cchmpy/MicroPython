class AccelerometerData:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
    def __eq__(self, other):        
        if not isinstance(other, AccelerometerData):
            return False 
        epsilon = 0.01                                # 允许的误差
        return (abs(self.x - other.x) < epsilon and
               abs(self.y - other.y) < epsilon and
               abs(self.z - other.z) < epsilon)
data1 = AccelerometerData(1.0, 2.0, 3.0)
data2 = AccelerometerData(1.01, 1.99, 3.0)
print(data1 == data2)                                  # 输出: True（在误差范围内）
