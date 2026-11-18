def count_up_to(max):      # 生成器函数
    count = 1
    while count <= max:
        yield count        # 每次迭代返回一个值，下次从此处继续
        count += 1
generator = count_up_to(3) # 调用生成器函数会返回一个生成器对象
while True:
    try:
        print(next(generator)) # 按行依次输出: 1 2 3
    except StopIteration:
        break
for x in count_up_to(3):   # 迭代生成器对象
    print(x,end=' ')       # 输出: 1 2 3
