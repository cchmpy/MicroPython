import re
r,s = "<.*?>","<a> b <c>" 
mt = re.search(r,s)           # 无锚定，搜索成功
print(type(mt),mt.group(0))   # <class 'match'> <a>
mt = re.search("^"+r,s)       # 锚定开头，搜索成功
print(type(mt),mt.group(0))   # <class 'match'> <a>
mt = re.search(r+"$",s)       # 锚定末尾，验证整个字符串，搜索成功
print(type(mt),mt.group(0))   # <class 'match'> <a> b <c>
mt = re.search(r,"<hello")    # 搜索失败
print(mt)                     # None

