def create_rounder(decimals):    
    def round_number(x):                # 嵌套函数：固定 decimals 参数
        return round(x, decimals)
    return round_number
round_to_2 = create_rounder(2)
round_to_4 = create_rounder(4)
print(round_to_2(3.14159))              # 输出: 3.14
print(round_to_4(3.14159))               # 输出: 3.1416
