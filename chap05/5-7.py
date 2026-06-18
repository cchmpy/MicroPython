import btree
try:
    f=open('db.btree','rb+')   # 若文件存在，则二进制模式打开，可读可写，文件指针在开头
except OSError:
    f=open('db.btree','wb+')   # 若文件不存在，以二进制模式创建文件，可读可写，文件指针在开头
db = btree.open(f)             # 基于文件流打开数据库

# 添加或修改数据项
keys,values = (b'a','b','c','d'),(b'apple','banana','cherry','durian')
for k,v in zip(keys,values):
    db[k] = v

# 刷新数据库
db.flush()

# 删除
if 'd' in db: del db['d']

# 查询键对应值
print(db['a'])       # 输出: b'apple'
print(db.get('x'))   # 键不存在，输出: None

# 迭代
for k,v in db.items('c','a',btree.DESC | btree.INCL):  print(k,v)

# 必须执行的关闭操作   
db.close()
f.close()
