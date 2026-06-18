import array
a = array.array('I',[300,400,500])
b = array.array('B',[30,40,50])
a.extend(array.array('I',[600,700]))# 使用同类型数组扩充
a.extend(b'\x01\x02\x00\x00\x12')   # 有效，将4个字节识别为一个元素,最后一个字节舍弃
a.extend(b)                         # 无效，字节数不够
print(a)                            # 输出: array('I', [300, 400, 500, 600, 700, 513])
b.extend(a)                         # 有效，将a中的一个元素拆分为4个元素,等同于b+=a
print(len(b))                       # 输出: 27
