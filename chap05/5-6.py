from collections import namedtuple
bitmap_fmt = namedtuple('bitmap_fmt',('w','h','data')) # 定义保存位图信息的命名元组
def get_bitmap():
    ...
    w,h = 10,10
    return bitmap_fmt(w,h,b'0'*(w*h))                  # 返回一个命名元组对象
bm = get_bitmap()
print(bm.w,bm.h,len(bm.data))                          # 通过字段名访问，输出: 10 10 100
