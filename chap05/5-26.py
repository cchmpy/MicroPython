with open('1.txt') as fin, open('2.txt','w') as fout:
    buf_size = 256                                  # 缓冲区大写
    buf = memoryview(bytearray(buf_size))           # 用于读取缓冲
    f_size = fin.seek(0,2)                          # 获取文件大小
    fin.seek(0)                                     # 重新定位到文件开头
    while size := fin.readinto(buf):
        for i in range(size):
            if 97<=buf[i]<=122: buf[i]-=32          # 小写转大写，原地操作
        if size == buf_size: fout.write(buf)        # 写入整个buf
        else: fout.write(buf[:size])                # 写入部分buf
        print(f'{fin.tell()/f_size:0.2%}\r',end='') # 单行打印处理进度 
