import uctypes
from uctypes import sizeof
data = bytearray(64)
addr = uctypes.addressof(data)
d1 = {'arr':(0 | uctypes.ARRAY, 5 | uctypes.UINT32)}
d2 = (0 | uctypes.ARRAY, 5 | uctypes.UINT32)
s1 = uctypes.struct(addr,d1)
s2 = uctypes.struct(addr,d2)
print(sizeof(d1),sizeof(d2),sizeof(s1),sizeof(s2)) # 输出20 20 20 20