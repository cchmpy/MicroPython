from uctypes import UINT8, UINT32, struct, addressof
data = bytearray(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b')  # 定义目标内存
addr = addressof(data)             # 目标内存的地址
# 标量描述符，标量类型
desc1 = {'a': 0 | UINT8,
         'b': 1 | UINT8,
         'c': 2 | UINT8,
         'd': 3 | UINT8}
s1 = struct(addr,desc1)            # 定义结构体对象
print(s1.a, s1.b, s1.c, s1.d)      # 读取，通过结构体的“.”操作符,输出：0 1 2 3
s1.a = 0xff                        # 写入，s1.a对应内存的值为255

# 嵌套或递归结构的描述符
desc2 = {'x': 0 | UINT32,
         'y': 4 | UINT32,
         'v': (8, desc1)}
s1 = struct(addr,desc2)            # 定义结构体对象
print(hex(s1.x), hex(s1.y), s1.v.a)# 读取，输出：0x30201ff 0x7060504 8
s1.x = 0x03020100                  # 写入，s1.a对应内存的值为255
print(data[:4])                    # 输出：bytearray(b'\x00\x01\x02\x03')
