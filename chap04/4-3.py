import re
r,s = "<.*?>","<a> b <c>"     # 正则表达式字符串和目标字符串，模式是尖括号内含有0个或多个字符
mt = re.match(r,s)            # 无锚定，匹配成功
print(type(mt),mt.group(0))   # <class 'match'> <a>
mt = re.match("^"+r,s)        # 锚定开头，匹配成功
print(type(mt),mt.group(0))   # <class 'match'> <a>
mt = re.match(r+"$",s)        # 锚定末尾，验证整个字符串，匹配成功
print(type(mt),mt.group(0))   # <class 'match'> <a> b <c>
mt = re.match(r,"<hello")     # 匹配失败
print(mt)                     # None
