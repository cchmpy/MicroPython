from uctypes import UINT8, UINT16, ARRAY, struct, addressof
data = bytearray(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f')
addr = addressof(data)

# 数组元素是标量类型-----------------------------------------------
desc1 = {'x': 0 | UINT16,
         'y': 2 | UINT16,
         'arr': (4 | ARRAY, (len(data)-4) | UINT8)}
s1 = struct(addr,desc1)
print(hex(s1.x), hex(s1.y),s1.arr[0], s1.arr[1]) # 输出：0x100 0x302 4 5

# 数组元素是聚合类型-----------------------------------------------
desc2 = {'arr': (ARRAY, len(data)//2, {'x': 0 | UINT8, 'y': 1 | UINT8,})}
s2 = struct(addr,desc2)
for i in range(len(data)//2):
    print(s2.arr[i].x, s2.arr[i].y)   

# 元组作为描述符的一维数组-------------------------------------------
desc3 = (ARRAY, len(data) | UINT8)   # 2个数据项的元组作为描述符
a1 = struct(addr,desc3)
for i in range(len(data)):
    print(a1[i], end=' ')
print()

# 元组作为描述符的二维数组------------------------------------------- 
col, row = 4, len(data)//4           # 二维数组行列定义
sub = (ARRAY, col | UINT8)           # col个标量数据项
desc4 = (ARRAY, row, sub)            # row个聚合类型数据项
a2  = struct(addr, desc4)
for i in range(row):                 # 打印二维数组矩阵
    for j in range(col):
        print(a2[i][j],end=' ')
    print()
