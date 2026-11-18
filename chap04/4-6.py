import hashlib
buf_size = 4*1024                       # 缓冲区大写
buf = memoryview(bytearray(buf_size))   # 读取文件的缓冲
sha256 = hashlib.sha256()               # 构建sha256哈希对象
with open('sd/micropython.bin','rb') as f:    
    while (size:=f.readinto(buf)):      # 读取文件数据到缓存   
        if size == buf_size: sha256.update(buf)
        else: sha256.update(buf[:size]) # 最后一次读取的字节数通常不等于buf_size
print(sha256.digest().hex())            # 打印十六进制形式的哈希值

    