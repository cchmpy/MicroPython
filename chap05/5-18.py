import hashlib,binascii
buf_size = 4*1024                     # 缓冲区大写
buf = memoryview(bytearray(buf_size)) # 读取文件的缓冲
sha256 = hashlib.sha256()             # 构建sha256哈希对象

with open('micropython.bin','rb') as f:    
    while (size:=f.readinto(buf)):    # 读取文件数据到缓存   
        if size == buf_size:          # 避免使用切片（这会创建memoryview对象），节约内存
            sha256.update(buf)
        else:
            sha256.update(buf[:size]) # 最后一次读取的字节数通常不等于buf_size,需要切片

digest = binascii.hexlify(sha256.digest()) # 计算十六进制形式的bytes
print(digest) # 类似：b'5115867455b34c9d1af06d863c8ea08e7089e7086dd14dc517e8ffa8b0112832'


    