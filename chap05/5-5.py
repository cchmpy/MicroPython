from collections import OrderedDict
a = OrderedDict(a=1,b=2,c=3)                        # dict(**kwargs)
b = OrderedDict({x:x**2 for x in range(3)},a=5,b=6) # dict(map, **kwargs)
c = OrderedDict([('a',1),('b',2),('c',3)],x=4,y=5)  # dict(map, **kwargs)
    
a |= b
for k,v in a.items():
    print(f'{k}:{v}', end=' ') # 输出: a:5 b:6 c:3 0:0 1:1 2:4

d = OrderedDict(sorted(a.items(),key=lambda x:x[1])) # 使用a创建按照值排序的有序字典
