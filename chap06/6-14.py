from uctypes import UINT8, UINT32, PTR, struct, addressof
import struct as STR
raw = bytearray(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f')
raw_addr = addressof(raw)                # 原始数据地址
data = STR.pack('@2IP',0,1,raw_addr)     # 结构体数据
addr = addressof(data)                   # 结构体数据地址

# 指针指向基本类型-------------------------------------------
desc1 = {'x': 0 | UINT32,
         'y': 4 | UINT32,
         'data': (8 | PTR, UINT32)}      # 2个数据项的元组作为描述符
p1 = struct(addr,desc1)
p1.data[0] = 255                         # 无效赋值
print(p1.x,p1.y, hex(p1.data[0]),hex(p1.data[1])) # 输出: 0 1 0x3020100 0x7060504
# 指针指向聚合类型-------------------------------------------
desc2 = {'x': 0 | UINT32,
         'y': 4 | UINT32,
         'data': (8 | PTR, {'a': UINT32, 'b': 4 | UINT32})}    
p2 = struct(addr,desc2)
p2.data[0].a = 0xaabbccdd                         # 有效赋值
print(hex(p2.data[0].a),hex(p2.data[0].b))        # 输出: 0xaabbccdd 0x7060504


