import deflate
buf_size = 4096
buf = memoryview(bytearray(buf_size))
# ------------压缩mpy.bin文件，生成压缩文件mpy.gz------------------
with open('mpy.bin','rb') as fin, open('mpy.gz','wb') as fout:
    file_size = fin.seek(0,2)
    fin.seek(0)     
    with deflate.DeflateIO(fout,deflate.GZIP,8) as d:         
        while (size:=fin.readinto(buf)):            
            if size == buf_size: d.write(buf)
            else: d.write(buf[:size])            
            print(f'压缩进度:{(fin.tell()/file_size):.2%} \r',end='') # 单行打印压缩进度百分比
print()  # 换行打印解压进度
# ------------解压缩文件mpy.gz，生成原始文件mpy1.bin------------------
with open('mpy.gz','rb') as fin, open('mpy1.bin','wb') as fout:
    file_size = fin.seek(0,2)
    fin.seek(0)
    with deflate.DeflateIO(fin,deflate.GZIP,8) as d:       
        while (size:=d.readinto(buf)):                       # size是解压后的大小         
            if size == buf_size: fout.write(buf) 
            else: fout.write(buf[:size])            
            print(f'解压进度:{(fin.tell()/file_size):.2%} \r',end='')