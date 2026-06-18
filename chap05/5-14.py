import re
# -----------------使用字符串替换-----------------
print(re.sub('\d+\+\d+','8*8','12345+560=?')) # 输出: 8*8=?
# --------使用字符串替换，包含分组反向引用--------
s = 'Harper lee is a good man'
regex = re.compile('^(\w+) (\w+)')
print(re.sub(regex,r'\2 \1',s))               # 输出: lee Harper is a good man
# ------------------使用函数替换------------------
def foo(match):
    f = match.group                           # 把匹配对象的group()方法赋值给f    
    t = f(2)[0]                               # 2号分组的首个字符
    return t.upper()+f(2)[1:]+' '+ f(1) if t.islower() else f(2)+' '+ f(1)    
print(re.sub(regex,foo,s))                    # 输出: Lee Harper is a good man
