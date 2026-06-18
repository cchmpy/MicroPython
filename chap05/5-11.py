import re
def match_fixed_digits(text, length):         # 用 \d* 匹配数字，再检查长度    
    mt = re.match(r"\d+", text)               # 匹配操作
    if mt and len(mt.group(0)) == length:     # 检查匹配结果
        return mt
    return None

print(match_fixed_digits("12345", 10))        # None（长度不符）
print(match_fixed_digits("2023512345", 10))   # <match num=1>
