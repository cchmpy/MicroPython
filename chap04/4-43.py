class DataPoint:
    def __init__(self, timestamp, value):
        self.timestamp = timestamp     # 整数时间戳（不可变）
        self.value = value
    def __eq__(self,other):
        return isinstance(other,DataPoint) and self.timestamp == other.timestamp
    def __hash__(self):
        return self.timestamp          # 直接使用时间戳作为哈希
unique_points = {DataPoint(1000, 25.5), DataPoint(1000, 26.0)}
print(len(unique_points))              # 输出: 1（时间戳相同去重）
