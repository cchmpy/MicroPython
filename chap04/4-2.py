import btree
try: f=open('db.btree','rb+')   # 若文件存在，二进制模式打开，可读写，文件指针在开头
except OSError: f=open('db.btree','wb+')   # 若文件不存在，以二进制模式创建文件
db = btree.open(f)                         # 基于文件流打开数据库
keys,values = (b'a','b','c','d'),(b'apple','banana','cherry','durian')
for k,v in zip(keys,values): db[k] = v     # 添加或修改数据项
db.flush()                                 # 刷新数据库
if 'd' in db: del db['d']                  # 删除数据项
print(db['a'])                             # 查询，输出: b'apple'
print(db.get('x'))                         # 查询，键不存在，输出: None
for k,v in db.items('c','a',btree.DESC | btree.INCL):  print(k,v)   # 迭代
db.close()                                 # 关闭数据库
f.close()                                  # 关闭底层流
