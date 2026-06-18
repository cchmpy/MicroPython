import array
# MicroPython支持的array类型码及其对应的C类型描述
codes = [['b', 'signed char'],['B', 'unsigned char'],
         ['h', 'signed short'],['H', 'unsigned short'],
         ['i', 'signed int'],['I', 'unsigned int'],
         ['l', 'signed long'],['L', 'unsigned long'],
         ['q', 'signed long long'],['Q', 'unsigned long long'],
         ['f', 'float'],['d', 'double']]

print(f"codes {'C类型描述':<20} 字节数")
print("----------------------------")
for code in codes:    
    try:       
        arr = array.array(code[0], [1,2])   # 创建array数组
        size = len(bytes(arr))//len(arr)    # 计算数组每个元素占用的字节数
        print(f"'{code[0]}'   {code[1]:<18} {size}")
    except (ValueError,TypeError) as err:
        print(f"不支持类型'{code[0]}'",err)
